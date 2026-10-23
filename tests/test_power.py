import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from scoralyx_player.power import RtcWakePoweroff, wake_epoch


class PowerTests(unittest.TestCase):
    def test_parses_offset_timestamp_to_epoch(self):
        value = "2026-10-24T08:00:00+02:00"
        expected = int(datetime(2026, 10, 24, 6, tzinfo=timezone.utc).timestamp())
        self.assertEqual(wake_epoch(value, now=expected - 3600), expected)

    def test_rejects_timestamp_without_timezone_or_too_close(self):
        with self.assertRaisesRegex(ValueError, "fuseau"):
            wake_epoch("2026-10-24T08:00:00", now=0)
        with self.assertRaisesRegex(ValueError, "proche"):
            wake_epoch("1970-01-01T00:02:00+00:00", now=60)

    @patch("scoralyx_player.power.subprocess.run")
    def test_uses_only_the_privileged_rtc_helper(self, run):
        RtcWakePoweroff().poweroff_until(1_800_000_000)
        self.assertEqual(
            run.call_args.args[0],
            ["sudo", "-n", "/usr/local/sbin/scoralyx-player-rtcwake", "1800000000"],
        )


if __name__ == "__main__":
    unittest.main()
