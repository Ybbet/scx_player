import tempfile
import unittest
from pathlib import Path

from scoralyx_player.config import Config


class ConfigTests(unittest.TestCase):
    def test_builds_screen_and_api_urls(self):
        config = Config(site_url="https://club.example.org/site", machine_name="clubhouse-01")
        self.assertEqual(
            config.api_url("api_ecran", ecran="club-house"),
            "https://club.example.org/site/spip.php?page=api_ecran&ecran=club-house",
        )
        self.assertEqual(
            config.display_url("club-house"),
            "https://club.example.org/site/spip.php?page=affichage_ecran&ecran=club-house",
        )

    def test_loads_toml_and_rejects_invalid_interval(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "player.toml"
            path.write_text(
                '[server]\nsite_url="https://club.example.org"\n'
                '[player]\nmachine_name="clubhouse-01"\n'
                '[intervals]\nheartbeat=0\n', encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "heartbeat"):
                Config.load(path)

    def test_http_requires_explicit_development_opt_in(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "player.toml"
            path.write_text(
                '[server]\nsite_url="http://club.example.org"\n'
                '[player]\nmachine_name="clubhouse-01"\n', encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "HTTPS"):
                Config.load(path)


if __name__ == "__main__":
    unittest.main()

