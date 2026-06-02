from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Dict

from .schemas import LLMResult


def should_use_llm(mode: str, safety_level: int, session_action: str, text: str) -> bool:
    if safety_level != 0:
        return False
    if session_action != "continue":
        return False
    if mode in {"wordplay", "sleepy"}:
        return False
    if mode in {"adventure", "story"}:
        return True
    return mode == "chat" and len((text or "").strip()) >= 16


class LLMClient:
    def __init__(self) -> None:
        self.provider = os.getenv("LOCAL_LLM_PROVIDER", "mock")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

    def generate(self, mode: str, child_text: str, memory_context: Dict[str, str], fallback: str) -> LLMResult:
        if self.provider != "ollama":
            return LLMResult(text=fallback, used=False, provider="mock-template")

        prompt = self._build_prompt(mode, child_text, memory_context)
        body = json.dumps(
            {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            self.ollama_url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
            text = (payload.get("response") or "").strip()
            return LLMResult(text=text or fallback, used=bool(text), provider="ollama")
        except (urllib.error.URLError, OSError, ValueError, KeyError):
            return LLMResult(text=fallback, used=False, provider="ollama-fallback")

    def _build_prompt(self, mode: str, child_text: str, memory_context: Dict[str, str]) -> str:
        memory_summary = ", ".join(
            f"{key}={value}" for key, value in memory_context.items() if value
        ) or "memory=none"
        return (
            "You are a plush companion for a 5-year-old.\n"
            "Rules: short reply, warm, a little clumsy, one question max, no scolding, no secrets, no medical advice.\n"
            f"Mode: {mode}\n"
            f"Memory: {memory_summary}\n"
            f"Child said: {child_text}\n"
            "Reply in Japanese with 1-2 short sentences."
        )

