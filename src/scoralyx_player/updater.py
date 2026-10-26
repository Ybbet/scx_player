from __future__ import annotations

import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

GITHUB_RELEASE_API = "https://api.github.com/repos/Ybbet/scx_player/releases/latest"
GITHUB_ARCHIVE = "https://github.com/Ybbet/scx_player/archive/refs/tags/v{version}.zip"
_STABLE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:\+[0-9A-Za-z.-]+)?$")


def semver_key(value: str) -> tuple[int, int, int] | None:
    match = _STABLE.fullmatch(value.strip())
    return tuple(map(int, match.groups())) if match else None


def is_newer(candidate: str, current: str) -> bool:
    candidate_key, current_key = semver_key(candidate), semver_key(current)
    return candidate_key is not None and current_key is not None and candidate_key > current_key


def latest_stable_version(timeout: int = 10) -> str | None:
    request = urllib.request.Request(
        GITHUB_RELEASE_API,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "Scoralyx-Player"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read(65537).decode("utf-8"))
        tag = str(data.get("tag_name", "")) if isinstance(data, dict) else ""
        candidate = tag[1:] if tag.startswith("v") else tag
        return candidate if semver_key(candidate) is not None else None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, UnicodeDecodeError):
        return None


def installed_version() -> str:
    try:
        return version("scoralyx-player")
    except PackageNotFoundError:
        return ""


def install_release(target_version: str, timeout: int = 900) -> None:
    if semver_key(target_version) is None:
        raise ValueError("Version cible SemVer invalide.")
    archive = GITHUB_ARCHIVE.format(version=target_version)
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "--force-reinstall", archive],
        check=True,
        timeout=timeout,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    actual = installed_version()
    if actual != target_version:
        raise RuntimeError("La version installée ne correspond pas à la version autorisée.")


def restart_player(config_path: Path) -> None:
    import os

    os.execv(sys.executable, [sys.executable, "-m", "scoralyx_player", "--config", str(config_path), "run"])
