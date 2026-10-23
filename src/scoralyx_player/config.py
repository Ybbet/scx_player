from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

DEFAULT_CONFIG = Path("/etc/scoralyx-player/config.toml")
DEFAULT_STATE = Path("/var/lib/scoralyx-player/state.json")


@dataclass(frozen=True)
class Config:
    site_url: str
    machine_name: str
    allow_insecure_http: bool = False
    display_path: str = "/spip.php?page=affichage_ecran"
    browser: str = "chromium"
    config_interval: int = 60
    heartbeat_interval: int = 60
    trigger_interval: int = 60
    enrollment_interval: int = 15
    request_timeout: int = 15
    config_path: Path = DEFAULT_CONFIG
    state_path: Path = DEFAULT_STATE

    @classmethod
    def load(cls, path: Path | None = None) -> "Config":
        config_path = Path(os.environ.get("SCORALYX_PLAYER_CONFIG", path or DEFAULT_CONFIG))
        with config_path.open("rb") as stream:
            data = tomllib.load(stream)
        player = data.get("player", {})
        server = data.get("server", {})
        paths = data.get("paths", {})
        intervals = data.get("intervals", {})
        site_url = str(server.get("site_url", "")).strip().rstrip("/")
        machine_name = str(player.get("machine_name", "")).strip()
        if not site_url.startswith(("https://", "http://")):
            raise ValueError("server.site_url doit être une URL HTTP ou HTTPS.")
        allow_insecure_http = server.get("allow_insecure_http", False)
        if not isinstance(allow_insecure_http, bool):
            raise ValueError("server.allow_insecure_http doit être un booléen TOML.")
        if site_url.startswith("http://") and not allow_insecure_http:
            raise ValueError("HTTPS est requis. Pour un environnement de test uniquement, activer server.allow_insecure_http.")
        if not machine_name:
            raise ValueError("player.machine_name est obligatoire.")
        parsed = urlsplit(site_url)
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("server.site_url ne doit contenir ni identifiants, ni paramètres, ni fragment.")
        state_path = Path(paths.get("state", DEFAULT_STATE)).expanduser()
        return cls(
            site_url=site_url,
            machine_name=machine_name,
            allow_insecure_http=allow_insecure_http,
            display_path=str(paths.get("display", "/spip.php?page=affichage_ecran")),
            browser=str(player.get("browser", "chromium")),
            config_interval=_positive(intervals.get("configuration", 60), "intervals.configuration"),
            heartbeat_interval=_positive(intervals.get("heartbeat", 60), "intervals.heartbeat"),
            trigger_interval=_positive(intervals.get("actualisation", 60), "intervals.actualisation"),
            enrollment_interval=_positive(intervals.get("enrollment", 15), "intervals.enrollment"),
            request_timeout=_positive(intervals.get("request_timeout", 15), "intervals.request_timeout"),
            config_path=config_path,
            state_path=state_path,
        )

    def api_url(self, page: str, **params: str) -> str:
        base = urlsplit(self.site_url)
        query = {"page": page, **params}
        return urlunsplit((base.scheme, base.netloc, f"{base.path.rstrip('/')}/spip.php", urlencode(query), ""))

    def display_url(self, screen_id: str) -> str:
        base = urlsplit(self.site_url)
        path = self.display_path
        parsed_path = urlsplit(path)
        if parsed_path.scheme or parsed_path.netloc:
            raise ValueError("paths.display doit être un chemin relatif au site.")
        pairs = parse_qsl(parsed_path.query, keep_blank_values=True)
        params = dict(pairs)
        params["ecran"] = screen_id
        site_path = base.path.rstrip("/")
        display_path = f"{site_path}/{parsed_path.path.lstrip('/')}"
        return urlunsplit((base.scheme, base.netloc, display_path, urlencode(params), ""))


def _positive(value: object, key: str) -> int:
    number = int(value)
    if number < 1 or number > 86400:
        raise ValueError(f"{key} doit être compris entre 1 et 86400 secondes.")
    return number

