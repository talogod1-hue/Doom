"""Optional speech output. Uses the OS speech tool if present; otherwise stays silent."""

from __future__ import annotations

import shutil
import subprocess


def _speaker_command() -> list[str] | None:
    if shutil.which("say"):                 # macOS
        return ["say"]
    if shutil.which("espeak"):              # Linux
        return ["espeak"]
    if shutil.which("espeak-ng"):
        return ["espeak-ng"]
    return None


class Voice:
    def __init__(self, enabled: bool = True) -> None:
        self.command = _speaker_command() if enabled else None

    @property
    def available(self) -> bool:
        return self.command is not None

    def speak(self, text: str) -> None:
        if not self.command:
            return
        try:
            subprocess.run(self.command + [text], check=False, timeout=120)
        except (OSError, subprocess.TimeoutExpired):
            pass
