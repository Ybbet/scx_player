import unittest
from unittest.mock import patch

from scoralyx_player.updater import is_newer, semver_key


class UpdaterTests(unittest.TestCase):
    def test_accepts_only_stable_semver(self):
        self.assertEqual(semver_key("0.6.0"), (0, 6, 0))
        self.assertEqual(semver_key("1.2.3+build.5"), (1, 2, 3))
        self.assertIsNone(semver_key("1.2.3-rc.1"))
        self.assertIsNone(semver_key("latest"))
        self.assertFalse(is_newer("0.5.1", "0.6.0"))
        self.assertTrue(is_newer("0.6.0", "0.5.1"))

    def test_latest_release_rejects_prerelease_or_invalid_tags(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *_args): return False
            def read(self, _size): return b'{"tag_name":"v0.6.0"}'

        with patch("scoralyx_player.updater.urllib.request.urlopen", return_value=Response()):
            from scoralyx_player.updater import latest_stable_version
            self.assertEqual(latest_stable_version(), "0.6.0")


if __name__ == "__main__":
    unittest.main()
