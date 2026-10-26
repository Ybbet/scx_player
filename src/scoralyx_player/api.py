from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from . import __version__
from .config import Config


class ApiError(RuntimeError):
    def __init__(self, message: str, status: int | None = None, payload: Any = None):
        super().__init__(message)
        self.status = status
        self.payload = payload


class ScoralyxApi:
    def __init__(self, config: Config):
        self.config = config

    def request(self, method: str, url: str, payload: dict | None = None, token: str = "") -> dict:
        headers = {"Accept": "application/json", "User-Agent": f"Scoralyx-Player/{__version__}"}
        body = None
        if payload is not None:
            headers["Content-Type"] = "application/json; charset=utf-8"
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers.update(authenticated_headers(token))
        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=self.config.request_timeout) as response:
                raw = response.read(65537)
                if len(raw) > 65536:
                    raise ApiError("Réponse SPIP supérieure à 64 Kio.", response.status)
                return _decode(raw, response.status)
        except urllib.error.HTTPError as error:
            raw = error.read(65537)
            try:
                data = _decode(raw, error.code)
            except ApiError:
                data = {}
            if token:
                data = _redact_token(data, token)
            raise ApiError(f"Réponse HTTP {error.code} de SPIP.", error.code, data) from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise ApiError("SPIP est injoignable.") from None

    def register(self, installation_id: str, machine_name: str) -> dict:
        return self.request("POST", self.config.api_url("api_ecran_enregistrement"), {
            "action": "register",
            "installation_id": installation_id,
            "machine_name": machine_name,
            "player_version": __version__,
        })

    def enrollment_status(self, installation_id: str, secret: str) -> dict:
        return self.request("POST", self.config.api_url("api_ecran_enregistrement"), {
            "action": "status",
            "installation_id": installation_id,
            "enrollment_secret": secret,
        })

    def configuration(self, screen_id: str, token: str) -> dict:
        return self.request("GET", self.config.api_url("api_ecran", ecran=screen_id), token=token)

    def heartbeat(self, screen_id: str, token: str, data: dict) -> dict:
        return self.request("POST", self.config.api_url("api_ecran_heartbeat"), {"screen": screen_id, **data}, token)

    def event(self, screen_id: str, token: str, data: dict) -> dict:
        return self.request("POST", self.config.api_url("api_ecran_evenement"), {"screen": screen_id, **data}, token)

    def trigger(self, screen_id: str, token: str, trigger_type: str) -> dict:
        return self.request("POST", self.config.api_url("api_ecran_declenchement"), {
            "screen": screen_id,
            "type": trigger_type,
        }, token)

    def update_status(self, screen_id: str, token: str, request_id: str, status: str, message: str = "") -> dict:
        payload = {"screen": screen_id, "request_id": request_id, "status": status}
        if message:
            payload["message"] = message[:500]
        return self.request("POST", self.config.api_url("api_ecran_mise_a_jour"), payload, token)


def _decode(raw: bytes, status: int) -> dict:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ApiError("SPIP a renvoyé une réponse JSON invalide.", status) from error
    if not isinstance(value, dict):
        raise ApiError("La réponse JSON de SPIP doit être un objet.", status)
    return value


def authenticated_headers(token: str) -> dict[str, str]:
    """Construire les headers communs aux requêtes avec le jeton définitif."""
    if not token:
        return {}
    bearer = f"Bearer {token}"
    return {
        "Authorization": bearer,
        "X-Scoralyx-Authorization": bearer,
    }


def _redact_token(value: Any, token: str) -> Any:
    """Éviter qu'une réponse d'erreur du serveur ne réexpose le jeton."""
    if isinstance(value, str):
        return value.replace(token, "[REDACTED]")
    if isinstance(value, list):
        return [_redact_token(item, token) for item in value]
    if isinstance(value, dict):
        return {
            key.replace(token, "[REDACTED]") if isinstance(key, str) else key: _redact_token(item, token)
            for key, item in value.items()
        }
    return value

