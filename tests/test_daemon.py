import tempfile
import unittest
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


class DaemonTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()

