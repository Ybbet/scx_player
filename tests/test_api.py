import io
import json
import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from scoralyx_player.api import ApiError, ScoralyxApi, authenticated_headers
from scoralyx_player.config import Config
from scoralyx_player.daemon import Player


TOKEN = "scx_secret_token_never_log"


class FakeResponse:
    status = 200

    def __init__(self, payload):
        self.raw = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _size=-1):
        return self.raw


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.config = Config(
            site_url="https://club.example.org",
            machine_name="clubhouse-01",
            state_path=Path(tempfile.gettempdir()) / "scoralyx-player-api-test-state.json",
        )
        self.api = ScoralyxApi(self.config)

    @staticmethod
    def _headers(request):
        return {name.lower(): value for name, value in request.header_items()}

    def test_authenticated_headers_are_centralized_and_used_by_every_endpoint(self):
        self.assertEqual(
            authenticated_headers(TOKEN),
            {
                "Authorization": f"Bearer {TOKEN}",
                "X-Scoralyx-Authorization": f"Bearer {TOKEN}",
            },
        )
        requests = []

        def open_request(request, timeout):
            requests.append(request)
            return FakeResponse({"ok": True})

        with patch("scoralyx_player.api.urllib.request.urlopen", side_effect=open_request):
            self.api.configuration("clubhouse", TOKEN)
            self.api.heartbeat("clubhouse", TOKEN, {"state": "on"})
            self.api.event("clubhouse", TOKEN, {"type": "player_connected"})
            self.api.trigger("clubhouse", TOKEN, "actualisation")
            self.api.update_status("clubhouse", TOKEN, "upd_123", "acknowledged")

        self.assertEqual(len(requests), 5)
        for request in requests:
            headers = self._headers(request)
            self.assertEqual(headers["authorization"], f"Bearer {TOKEN}")
            self.assertEqual(headers["x-scoralyx-authorization"], f"Bearer {TOKEN}")
            self.assertNotIn(TOKEN, request.full_url)
        update_request = requests[-1]
        self.assertTrue(update_request.full_url.endswith("page=api_ecran_mise_a_jour"))
        self.assertEqual(json.loads(update_request.data), {
            "screen": "clubhouse", "request_id": "upd_123", "status": "acknowledged",
        })

    def test_registration_and_enrollment_status_do_not_use_final_token_headers(self):
        requests = []

        def open_request(request, timeout):
            requests.append(request)
            return FakeResponse({"status": "pending"})

        with patch("scoralyx_player.api.urllib.request.urlopen", side_effect=open_request):
            self.api.register("install-id", "clubhouse-01")
            self.api.enrollment_status("install-id", "enrollment-secret")

        self.assertEqual(len(requests), 2)
        for request in requests:
            headers = self._headers(request)
            self.assertNotIn("authorization", headers)
            self.assertNotIn("x-scoralyx-authorization", headers)
            self.assertNotIn(TOKEN, request.full_url)

    def test_first_configuration_call_after_approval_uses_both_headers(self):
        requests = []
        responses = [
            FakeResponse({
                "status": "approved",
                "token": TOKEN,
                "screen_info": {"id": "clubhouse", "name": "Club-house"},
            }),
            FakeResponse({"api_version": 1, "screen": {"id": "clubhouse"}}),
        ]

        def open_request(request, timeout):
            requests.append(request)
            return responses.pop(0)

        with tempfile.TemporaryDirectory() as directory:
            config = Config(
                site_url="https://club.example.org",
                machine_name="clubhouse-01",
                state_path=Path(directory) / "state.json",
            )
            api = ScoralyxApi(config)
            player = Player(config, api=api)
            player.state.enrollment_secret = "enrollment-secret"
            with patch("scoralyx_player.api.urllib.request.urlopen", side_effect=open_request):
                player._enrollment_step()
                api.configuration(player.state.screen_id, player.state.token)

        self.assertEqual(len(requests), 2)
        enrollment_headers = self._headers(requests[0])
        self.assertNotIn("authorization", enrollment_headers)
        self.assertNotIn("x-scoralyx-authorization", enrollment_headers)
        config_headers = self._headers(requests[1])
        self.assertEqual(config_headers["authorization"], f"Bearer {TOKEN}")
        self.assertEqual(config_headers["x-scoralyx-authorization"], f"Bearer {TOKEN}")
        self.assertNotIn(TOKEN, requests[1].full_url)

    def test_token_is_redacted_from_http_errors_and_never_logged(self):
        url = self.config.api_url("api_ecran", ecran="clubhouse")
        response_body = json.dumps({"error": "unauthorized", "debug": TOKEN, TOKEN: "echo"}).encode()
        http_error = HTTPError(url, 401, "Unauthorized", {}, io.BytesIO(response_body))
        log_output = io.StringIO()
        handler = logging.StreamHandler(log_output)
        logger = logging.getLogger("scoralyx_player.api")
        previous_level = logger.level
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        try:
            with patch("scoralyx_player.api.urllib.request.urlopen", side_effect=http_error):
                with self.assertRaises(ApiError) as caught:
                    self.api.configuration("clubhouse", TOKEN)
        finally:
            logger.removeHandler(handler)
            logger.setLevel(previous_level)

        error = caught.exception
        self.assertEqual(error.status, 401)
        self.assertNotIn(TOKEN, str(error))
        self.assertNotIn(TOKEN, repr(error))
        self.assertNotIn(TOKEN, json.dumps(error.payload))
        self.assertIsNone(error.__cause__)
        self.assertNotIn(TOKEN, log_output.getvalue())


if __name__ == "__main__":
    unittest.main()
