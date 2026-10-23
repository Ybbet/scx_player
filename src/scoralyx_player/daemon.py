from __future__ import annotations

import logging
import signal
import socket
import subprocess
import time
import uuid
from datetime import datetime, timezone

from . import API_VERSION, __version__
from .api import ApiError, ScoralyxApi
from .browser import BLACK_PAGE, Browser
from .config import Config
from .power import RtcWakePoweroff, wake_epoch
from .state import PlayerState

LOG = logging.getLogger(__name__)


class Player:
    def __init__(self, config: Config, api: ScoralyxApi | None = None, browser: Browser | None = None, power=None):
        self.config = config
        self.api = api or ScoralyxApi(config)
        self.browser = browser or Browser(config.browser, config.state_path.parent / "chromium-profile")
        self.power = power or RtcWakePoweroff()
        self.state = PlayerState.load(config.state_path)
        if not self.state.installation_id:
            self.state.installation_id = str(uuid.uuid4())
            self.state.save(config.state_path)
        self.started = time.monotonic()
        self.stop_requested = False
        self.last_config = 0.0
        self.last_heartbeat = 0.0
        self.last_trigger = 0.0
        self.last_event_state = ""
        self.startup_announced = False
        self.pending_wake_epoch: int | None = None
        self.last_poweroff_attempt: tuple[int, float] | None = None
        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT, self.stop)

    def stop(self, *_args) -> None:
        self.stop_requested = True

    def run(self) -> None:
        LOG.info("Scoralyx Player %s démarre sur %s.", __version__, self.config.machine_name)
        backoff = 2
        while not self.stop_requested:
            try:
                if not self.state.token:
                    self._enrollment_step()
                    self._wait(self.config.enrollment_interval)
                    continue
                config = self._configuration()
                now = time.monotonic()
                if self._configuration_refresh_due(now, config):
                    config = self._fetch_configuration()
                self._apply_state(config)
                if now - self.last_heartbeat >= self.config.heartbeat_interval:
                    self._send_heartbeat(config)
                if self.pending_wake_epoch is not None:
                    self._poweroff_for_wakeup(self.pending_wake_epoch)
                if getattr(self, "player_state", "off") == "on" and "actualisation" in config.get("capabilities", {}).get("triggers", []) and now - self.last_trigger >= self.config.trigger_interval:
                    self._send_trigger()
                backoff = 2
                self._wait(1)
            except ApiError as error:
                if error.status in (401, 403):
                    LOG.error("Accès Player refusé (HTTP %s). Vérifier l'autorisation dans SPIP ; nouvelle tentative dans 5 minutes.", error.status)
                    self._wait(300)
                else:
                    LOG.warning("Échange avec SPIP en échec : %s", error)
                    self._wait(backoff)
                    backoff = min(backoff * 2, 300)
            except Exception:
                LOG.exception("Erreur inattendue du Player.")
                self._wait(backoff)
                backoff = min(backoff * 2, 300)
        self.browser.close()
        LOG.info("Scoralyx Player arrêté.")

    def _enrollment_step(self) -> None:
        if not self.state.enrollment_secret:
            try:
                result = self.api.register(self.state.installation_id, self.config.machine_name)
            except ApiError as error:
                if error.status == 409 and isinstance(error.payload, dict):
                    LOG.error("Cette installation est déjà connue de SPIP (%s). Restaurer son état local ou révoquer l'ancien Player.", error.payload.get("status", "inconnu"))
                    self._wait(60)
                    return
                raise
            self.state.enrollment_secret = str(result.get("enrollment_secret", ""))
            self.state.pairing_code = str(result.get("pairing_code", ""))
            self.state.save(self.config.state_path)
            LOG.info("Demande d'enrôlement créée. Code à saisir dans SPIP : %s", self.state.pairing_code)
            return
        result = self.api.enrollment_status(self.state.installation_id, self.state.enrollment_secret)
        status = result.get("status")
        if status == "pending":
            self.state.pairing_code = str(result.get("pairing_code", self.state.pairing_code))
            LOG.info("Enrôlement en attente (code %s).", self.state.pairing_code)
        elif status == "approved":
            screen = result.get("screen_info") or {"id": result.get("screen", ""), "name": ""}
            self.state.token = str(result.get("token", ""))
            self.state.screen_id = str(screen.get("id", ""))
            self.state.screen_name = str(screen.get("name", ""))
            self.state.enrollment_secret = "" if self.state.token else self.state.enrollment_secret
            self.state.pairing_code = ""
            self.state.save(self.config.state_path)
            if not self.state.token or not self.state.screen_id:
                raise ApiError("SPIP a autorisé le Player sans remettre de jeton ou d'identifiant d'écran.")
            LOG.info("Player associé à l'écran %s (%s).", self.state.screen_name, self.state.screen_id)
        elif status in ("rejected", "revoked"):
            raise ApiError(f"Demande d'enrôlement {status}.", 403, result)

    def _configuration(self) -> dict | None:
        return getattr(self, "server_configuration", None)

    def _configuration_refresh_due(self, now: float, config: dict | None) -> bool:
        if config is None or now - self.last_config >= self.config.config_interval:
            return True
        state = config.get("state") or {}
        transition = state.get("next_stop") if state.get("expected") == "on" else state.get("next_start")
        if not transition:
            return False
        try:
            when = datetime.fromisoformat(str(transition).replace("Z", "+00:00"))
            if when.tzinfo is None:
                return False
            return (when.astimezone(timezone.utc) - datetime.now(timezone.utc)).total_seconds() <= 15
        except ValueError:
            return False

    def _fetch_configuration(self) -> dict:
        config = self.api.configuration(self.state.screen_id, self.state.token)
        if config.get("api_version") != API_VERSION:
            raise ApiError(f"Version d'API Player non prise en charge : {config.get('api_version')}.")
        screen = config.get("screen") or {}
        if str(screen.get("id", "")) != self.state.screen_id:
            raise ApiError("L'identifiant d'écran retourné par SPIP ne correspond pas au Player.")
        player = config.get("player") or {}
        if player.get("machine_name") and player["machine_name"] != self.config.machine_name:
            raise ApiError("Le nom machine retourné par SPIP ne correspond pas à la configuration locale.")
        self.state.screen_name = str(screen.get("name", self.state.screen_name))
        previous_version = self.state.configuration_version
        self.state.configuration_version = int((config.get("settings") or {}).get("configuration_version", 0))
        self.state.save(self.config.state_path)
        self.server_configuration = config
        self.last_config = time.monotonic()
        if not self.startup_announced:
            self._send_event("player_starting", "info")
            self.startup_announced = True
        elif previous_version and previous_version != self.state.configuration_version:
            self._send_event("configuration_applied", "succes")
        LOG.info("Configuration reçue pour %s ; état attendu : %s.", self.state.screen_name, (config.get("state") or {}).get("expected"))
        return config

    def _apply_state(self, config: dict) -> None:
        expected = (config.get("state") or {}).get("expected")
        if expected not in ("on", "off"):
            raise ApiError(f"État attendu invalide : {expected!r}.")
        url = self.config.display_url(self.state.screen_id) if expected == "on" else BLACK_PAGE
        changed = self.browser.ensure(url)
        if changed and expected == "on":
            self._send_event("browser_operational", "succes")
        if changed and expected == "off":
            LOG.info("Écran logique éteint : navigateur placé sur un écran noir.")
        self.display_state = "visible" if expected == "on" else "blank"
        self.player_state = expected
        self.pending_wake_epoch = None
        if expected == "off" and self.config.rtcwake_enabled:
            next_start = (config.get("state") or {}).get("next_start")
            try:
                if next_start:
                    self.pending_wake_epoch = wake_epoch(next_start)
            except ValueError as error:
                LOG.warning("Arrêt RTC non programmé : %s", error)
        if expected != self.last_event_state:
            if expected == "on":
                self._send_event("player_connected", "succes")
            self.last_event_state = expected

    def _poweroff_for_wakeup(self, epoch: int) -> None:
        now = time.monotonic()
        if self.last_poweroff_attempt and self.last_poweroff_attempt[0] == epoch and now - self.last_poweroff_attempt[1] < 300:
            return
        self.last_poweroff_attempt = (epoch, now)
        self._send_event("shutdown_requested", "info")
        try:
            self.power.poweroff_until(epoch)
        except (OSError, subprocess.SubprocessError) as error:
            LOG.error("Arrêt avec réveil RTC impossible ; maintien du Player sur écran noir : %s", error)
            self._send_event("incident", "attention")
            return
        LOG.info("Réveil RTC programmé ; arrêt de la machine jusqu'à %s.", datetime.fromtimestamp(epoch).astimezone().isoformat())

    def _send_event(self, event_type: str, level: str) -> None:
        try:
            self.api.event(self.state.screen_id, self.state.token, {
                "event_id": str(uuid.uuid4()),
                "type": event_type,
                "level": level,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "message": "",
                "data": {"player_version": __version__},
            })
        except ApiError:
            LOG.exception("Impossible de transmettre l'événement %s.", event_type)

    def _send_heartbeat(self, config: dict) -> None:
        self.api.heartbeat(self.state.screen_id, self.state.token, {
            "player_time": datetime.now().astimezone().isoformat(),
            "state": getattr(self, "player_state", "off"),
            "display_state": getattr(self, "display_state", "blank"),
            "browser": "running" if self.browser.running() else "stopped",
            "display_connected": "unknown",
            "uptime": max(0, int(time.monotonic() - self.started)),
            "player_version": __version__,
            "browser_version": self.browser.version(),
            "configuration_version": self.state.configuration_version,
        })
        self.last_heartbeat = time.monotonic()

    def _send_trigger(self) -> None:
        try:
            result = self.api.trigger(self.state.screen_id, self.state.token, "actualisation")
        except ApiError as error:
            if error.status in (403, 422):
                LOG.warning("Déclenchement actualisation refusé par SPIP : %s", error.payload or error)
                self.last_trigger = time.monotonic()
                return
            raise
        self.last_trigger = time.monotonic()
        LOG.debug("Déclenchement actualisation transmis : %s.", result.get("status", "inconnu"))

    def _wait(self, seconds: int) -> None:
        deadline = time.monotonic() + seconds
        while not self.stop_requested and time.monotonic() < deadline:
            time.sleep(min(0.5, deadline - time.monotonic()))

