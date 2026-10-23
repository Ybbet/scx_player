import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scoralyx_player.browser import BLACK_PAGE
from scoralyx_player.config import Config
from scoralyx_player.daemon import Player


class FakeApi:
    def __init__(self):
        self.events = []

    def event(self, screen_id, token, data):
        self.events.append(data)


class FakeBrowser:
    def __init__(self):
        self.urls = []

    def ensure(self, url):
        self.urls.append(url)
        return True


class FakePower:
    def __init__(self):
        self.wake_epochs = []

    def poweroff_until(self, epoch):
        self.wake_epochs.append(epoch)


class DaemonTests(unittest.TestCase):
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

