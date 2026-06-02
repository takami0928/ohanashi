from __future__ import annotations

import base64
import json
import os
import urllib.parse
import urllib.request

from .schemas import Settings, TTSResult


class TTSClient:
    def __init__(self) -> None:
        self.provider = os.getenv("LOCAL_TTS_PROVIDER", "browser")
        self.voicevox_url = os.getenv("VOICEVOX_URL", "http://127.0.0.1:50021")
        self.speaker = int(os.getenv("VOICEVOX_SPEAKER", "1"))

    def synthesize(self, text: str, settings: Settings) -> TTSResult:
        if not settings.voice_enabled:
            return TTSResult(audio_base64=None, used=False, provider="voice-disabled")

        if self.provider == "voicevox":
            result = self._voicevox(text, settings)
            if result.audio_base64:
                return result

        return TTSResult(audio_base64=None, used=False, provider="browser-fallback")

    def _voicevox(self, text: str, settings: Settings) -> TTSResult:
        try:
            query_url = (
                f"{self.voicevox_url}/audio_query?"
                + urllib.parse.urlencode({"text": text, "speaker": self.speaker})
            )
            with urllib.request.urlopen(
                urllib.request.Request(query_url, method="POST"),
                timeout=8,
            ) as response:
                query_payload = json.loads(response.read().decode("utf-8"))
            query_payload["speedScale"] = float(settings.speech_rate)
            synthesis_body = json.dumps(query_payload).encode("utf-8")
            synthesis_url = (
                f"{self.voicevox_url}/synthesis?"
                + urllib.parse.urlencode({"speaker": self.speaker})
            )
            with urllib.request.urlopen(
                urllib.request.Request(
                    synthesis_url,
                    data=synthesis_body,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                ),
                timeout=12,
            ) as response:
                audio_bytes = response.read()
            return TTSResult(
                audio_base64=base64.b64encode(audio_bytes).decode("ascii"),
                used=True,
                provider="voicevox",
            )
        except Exception:
            return TTSResult(audio_base64=None, used=False, provider="voicevox-failed")

