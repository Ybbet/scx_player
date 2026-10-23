from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class PlayerState:
    installation_id: str
    enrollment_secret: str = ""
    pairing_code: str = ""
    token: str = ""
    screen_id: str = ""
    screen_name: str = ""
    configuration_version: int = 0

    @classmethod
    def load(cls, path: Path) -> "PlayerState":
        if not path.exists():
            return cls(installation_id="")
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(**{key: data.get(key, field.default) for key, field in cls.__dataclass_fields__.items()})

    def save(self, path: Path) -> None:
        path.parent.mkdir(mode=0o750, parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".scoralyx-player-", dir=path.parent)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(asdict(self), stream, ensure_ascii=False, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
            os.chmod(path, 0o600)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

