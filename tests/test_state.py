import json
import os
import tempfile
import unittest
from pathlib import Path

from scoralyx_player.state import PlayerState


class StateTests(unittest.TestCase):
    def test_saves_private_state_and_reads_it_back(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            state = PlayerState(installation_id="a1b2c3d4", token="scx_secret", screen_id="clubhouse")
            state.save(path)
            loaded = PlayerState.load(path)
            self.assertEqual(loaded, state)
            self.assertEqual(os.stat(path).st_mode & 0o777, 0o600)
            self.assertEqual(json.loads(path.read_text())["token"], "scx_secret")


if __name__ == "__main__":
    unittest.main()

