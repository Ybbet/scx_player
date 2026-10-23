from __future__ import annotations

import logging
import os
import signal
import shutil
import subprocess
import time

LOG = logging.getLogger(__name__)
BLACK_PAGE = "data:text/html,<html><head><meta name='viewport' content='width=device-width,initial-scale=1'></head><body style='margin:0;background:#000'></body></html>"


class Browser:
    def __init__(self, executable: str, profile_path=None):
        self.executable = shutil.which(executable) or executable
        self.profile_path = profile_path
        self.process: subprocess.Popen | None = None
        self.url = ""
        self._version: str | None = None

    def ensure(self, url: str) -> bool:
        if self.process and self.process.poll() is None and self.url == url:
            return False
        self.stop()
        command = [
            self.executable,
            "--kiosk",
            "--no-first-run",
            "--disable-infobars",
            "--disable-session-crashed-bubble",
            "--disable-translate",
            "--noerrdialogs",
        ]
        if self.profile_path:
            self.profile_path.mkdir(mode=0o700, parents=True, exist_ok=True)
            command.append(f"--user-data-dir={self.profile_path}")
        command.append(url)
        LOG.info("Démarrage du navigateur kiosque.")
        self.process = subprocess.Popen(command, close_fds=True, start_new_session=True)
        self.url = url
        return True

    def running(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def version(self) -> str:
        if self._version is None:
            try:
                result = subprocess.run([self.executable, "--version"], capture_output=True, text=True, timeout=5, check=False)
                self._version = (result.stdout or result.stderr).strip()[:128]
            except (OSError, subprocess.TimeoutExpired):
                self._version = ""
        return self._version

    def stop(self) -> None:
        process, self.process = self.process, None
        self.url = ""
        if not process or process.poll() is not None:
            return
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=5)

    def close(self) -> None:
        self.stop()

