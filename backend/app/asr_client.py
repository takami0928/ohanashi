from __future__ import annotations

import base64
import os
import subprocess
import tempfile

from .schemas import ASRResult


class ASRClient:
    def __init__(self) -> None:
        self.provider = os.getenv("LOCAL_ASR_PROVIDER", "mock")
        self.command = os.getenv("ASR_COMMAND", "").strip()

    def transcribe(self, audio_base64: str | None, text_fallback: str | None = None) -> ASRResult:
        if text_fallback:
            return ASRResult(text=text_fallback.strip(), success=True, provider="text-fallback")

        if not audio_base64:
            return ASRResult(text="", success=False, provider="missing-audio")

        if self.provider == "command" and self.command:
            return self._transcribe_with_command(audio_base64)

        return ASRResult(text="", success=False, provider="mock-asr")

    def _transcribe_with_command(self, audio_base64: str) -> ASRResult:
        audio_bytes = base64.b64decode(audio_base64)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name

        command = self.command.format(input=temp_path)
        try:
            completed = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            text = (completed.stdout or "").strip()
            return ASRResult(text=text, success=bool(text), provider="command")
        except (OSError, subprocess.SubprocessError):
            return ASRResult(text="", success=False, provider="command-failed")
        finally:
            try:
                os.remove(temp_path)
            except OSError:
                pass

