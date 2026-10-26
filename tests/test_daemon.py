import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse
from unittest.mock import patch

from scoralyx_player.browser import BLACK_PAGE
from scoralyx_player.config import Config
from scoralyx_player.daemon import Player


class FakeApi:
    def __init__(self):
        self.events = []
        self.update_statuses = []
        self.heartbeats = []

    def event(self, screen_id, token, data):
        self.events.append(data)

    def update_status(self, screen_id, token, request_id, status, message=""):
        self.update_statuses.append((request_id, status, message))

    def heartbeat(self, screen_id, token, data):
        self.heartbeats.append(data)
        return {"ok": True}


class FakeBrowser:
    def __init__(self):
        self.urls = []

    def ensure(self, url):
        self.urls.append(url)
        return True

    def running(self):
        return True

    def version(self):
        return "Chromium test"

    def close(self):
        pass


class FakePower:
    def __init__(self):
        self.wake_epochs = []

    def poweroff_until(self, epoch):
        self.wake_epochs.append(epoch)


class DaemonTests(unittest.TestCase):
    def test_heartbeat_announces_detected_stable_version(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Config(site_url="https://club.example.org", machine_name="clubhouse-01", state_path=Path(directory) / "state.json")
            api, browser = FakeApi(), FakeBrowser()
            player = Player(config, api=api, browser=browser)
            player.state.token = "token"
            player.state.screen_id = "clubhouse"
            player.latest_stable = "0.6.0"
            player._send_heartbeat({})
            self.assertEqual(api.heartbeats[0]["latest_stable_version"], "0.6.0")

    def test_only_authorized_and_verified_update_is_installed_and_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Config(site_url="https://club.example.org", machine_name="clubhouse-01", state_path=Path(directory) / "state.json")
            api, browser = FakeApi(), FakeBrowser()
            player = Player(config, api=api, browser=browser)
            player.state.token = "token"
            player.state.screen_id = "clubhouse"
            contract = {
                "status": "authorized", "authorized": True, "request_id": "upd_1",
                "target_version": "0.6.0", "latest_stable_version": "0.6.0",
            }
            with patch("scoralyx_player.daemon.latest_stable_version", return_value="0.6.0"), \
                 patch("scoralyx_player.daemon.installed_version", return_value="0.5.1"), \
                 patch("scoralyx_player.daemon.install_release") as install, \
                 patch("scoralyx_player.daemon.restart_player") as restart:
                player._process_update(contract)
            install.assert_called_once_with("0.6.0")
            restart.assert_called_once_with(config.config_path)
            self.assertEqual([status for _, status, _ in api.update_statuses], ["acknowledged", "in_progress", "completed"])

    def test_available_update_without_server_authorization_is_not_installed(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Config(site_url="https://club.example.org", machine_name="clubhouse-01", state_path=Path(directory) / "state.json")
            player = Player(config, api=FakeApi(), browser=FakeBrowser())
            with patch("scoralyx_player.daemon.install_release") as install:
                player._process_update({"status": "available", "target_version": "0.6.0"})
            install.assert_not_called()

    def test_detects_package_version_change_and_restarts(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Config(site_url="https://club.example.org", machine_name="clubhouse-01", state_path=Path(directory) / "state.json")
            player = Player(config, api=FakeApi(), browser=FakeBrowser())
            with patch("scoralyx_player.daemon.time.monotonic", return_value=100), \
                 patch("scoralyx_player.daemon.installed_version", return_value="0.6.1"), \
                 patch("scoralyx_player.daemon.restart_player") as restart:
                player._check_installed_package()
            restart.assert_called_once_with(config.config_path)

    def test_black_page_is_a_local_html_file_with_full_black_background(self):
        parsed = urlparse(BLACK_PAGE)
        self.assertEqual(parsed.scheme, "file")
        html = Path(unquote(parsed.path)).read_text(encoding="utf-8")
        self.assertIn("background: #000", html)
        self.assertIn("width: 100%", html)
        self.assertIn("height: 100%", html)

    def test_refreshes_configuration_near_server_transition(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Config(
                site_url="https://club.example.org",
                machine_name="clubhouse-01",
                state_path=Path(directory) / "state.json",
            )
            player = Player(config, api=FakeApi(), browser=FakeBrowser())
            player.last_config = time.monotonic()
            transition = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            self.assertTrue(player._configuration_refresh_due(time.monotonic(), {"state": {"expected": "on", "next_stop": transition}}))

    def test_expected_on_opens_screen_url_and_off_blanks_it(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Config(
                site_url="https://club.example.org",
                machine_name="clubhouse-01",
                state_path=Path(directory) / "state.json",
            )
            api, browser = FakeApi(), FakeBrowser()
            player = Player(config, api=api, browser=browser)
            player.state.token = "scx_test"
            player.state.screen_id = "clubhouse"
            player._apply_state({"state": {"expected": "on"}})
            player._apply_state({"state": {"expected": "off"}})
            self.assertEqual(browser.urls[0], "https://club.example.org/spip.php?page=affichage_ecran&ecran=clubhouse")
            self.assertEqual(browser.urls[1], BLACK_PAGE)
            self.assertEqual(player.player_state, "off")
            self.assertEqual(player.display_state, "blank")

    def test_rtc_poweroff_uses_server_next_start(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Config(
                site_url="https://club.example.org",
                machine_name="clubhouse-01",
                state_path=Path(directory) / "state.json",
                rtcwake_enabled=True,
            )
            api, browser, power = FakeApi(), FakeBrowser(), FakePower()
            player = Player(config, api=api, browser=browser, power=power)
            player.state.token = "scx_test"
            player.state.screen_id = "clubhouse"
            expected_epoch = int(time.time()) + 7200
            next_start = datetime.fromtimestamp(expected_epoch, timezone.utc).isoformat()
            player._apply_state({"state": {"expected": "off", "next_start": next_start}})
            self.assertEqual(player.pending_wake_epoch, expected_epoch)
            player._poweroff_for_wakeup(player.pending_wake_epoch)
            self.assertEqual(power.wake_epochs, [expected_epoch])
            self.assertEqual(api.events[-1]["type"], "shutdown_requested")


if __name__ == "__main__":
    unittest.main()

