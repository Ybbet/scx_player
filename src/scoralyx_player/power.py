from __future__ import annotations

import logging
import subprocess
from datetime import datetime

LOG = logging.getLogger(__name__)
DEFAULT_POWER_HELPER = "/usr/local/sbin/scoralyx-player-rtcwake"


def wake_epoch(value: object, now: float | None = None) -> int:
    """Parse a contract timestamp and reject ambiguous or stale wake times."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("La prochaine heure de réveil est absente.")
    normalized = value.strip().replace("Z", "+00:00")
    try:
        when = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise ValueError("La prochaine heure de réveil n'est pas une date ISO 8601 valide.") from error
    if when.tzinfo is None:
        raise ValueError("La prochaine heure de réveil doit inclure son fuseau horaire.")
    epoch = int(when.timestamp())
    current = datetime.now().timestamp() if now is None else now
    if epoch <= current + 60:
        raise ValueError("La prochaine heure de réveil est trop proche ou déjà passée.")
    if epoch > current + 30 * 24 * 60 * 60:
        raise ValueError("La prochaine heure de réveil dépasse la limite de 30 jours.")
    return epoch


class RtcWakePoweroff:
    """Request the one-purpose, root-owned helper installed by install.sh."""

    def __init__(self, helper: str = DEFAULT_POWER_HELPER, sudo: str = "sudo"):
        self.helper = helper
        self.sudo = sudo

    def poweroff_until(self, epoch: int) -> None:
        subprocess.run(
            [self.sudo, "-n", self.helper, str(epoch)],
            check=True,
            timeout=30,
            capture_output=True,
            text=True,
        )

