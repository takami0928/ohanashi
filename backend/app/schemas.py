from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any, Dict, List, Optional


MODE_CHAT = "chat"
MODE_ADVENTURE = "adventure"
MODE_WORDPLAY = "wordplay"
MODE_STORY = "story"
MODE_SLEEPY = "sleepy"
MODE_AMBIGUOUS = "ambiguous"

ALL_MODES = [
    MODE_CHAT,
    MODE_ADVENTURE,
    MODE_WORDPLAY,
    MODE_STORY,
    MODE_SLEEPY,
]


@dataclass
class ModeDecision:
    mode: str
    confidence: str = "medium"
    choices: List[str] = field(default_factory=list)
    reason: str = ""


@dataclass
class SafetyAssessment:
    level: int
    category: str
    template_key: str
    reason: str
    llm_allowed: bool
    memory_allowed: bool


@dataclass
class SessionState:
    session_id: str
    started_at: str
    turn_count: int = 0
    failure_count: int = 0
    pending_wrap_up: bool = False
    extended_once: bool = False
    last_mode: str = MODE_CHAT


@dataclass
class SessionDecision:
    action: str
    template_key: Optional[str] = None
    reason: str = ""


@dataclass
class MemoryCard:
    id: str
    category: str
    key: str
    value: str
    scope: str
    created_at: str
    updated_at: str
    expires_at: Optional[str] = None


@dataclass
class Settings:
    toy_name: str = "もこ"
    child_name: str = ""
    mode_chat_enabled: bool = True
    mode_adventure_enabled: bool = True
    mode_wordplay_enabled: bool = True
    mode_story_enabled: bool = True
    mode_sleepy_enabled: bool = True
    voice_enabled: bool = True
    speech_rate: float = 0.95
    energy: str = "gentle"
    session_limit_minutes: int = 8
    daily_limit_minutes: int = 25
    max_turns: int = 6
    debug_mode: bool = False

    def enabled_modes(self) -> List[str]:
        enabled = []
        if self.mode_chat_enabled:
            enabled.append(MODE_CHAT)
        if self.mode_adventure_enabled:
            enabled.append(MODE_ADVENTURE)
        if self.mode_wordplay_enabled:
            enabled.append(MODE_WORDPLAY)
        if self.mode_story_enabled:
            enabled.append(MODE_STORY)
        if self.mode_sleepy_enabled:
            enabled.append(MODE_SLEEPY)
        return enabled


@dataclass
class TurnRequest:
    session_id: str
    audio_base64: Optional[str] = None
    text_input: Optional[str] = None
    recording_seconds: int = 20
    debug: bool = False


@dataclass
class TurnResult:
    session_id: str
    mode: str
    safety_level: int
    state_label: str
    response_text: str
    audio_base64: Optional[str]
    used_llm: bool
    used_asr: bool
    used_tts: bool
    debug: Optional[Dict[str, Any]] = None


@dataclass
class ASRResult:
    text: str
    success: bool
    provider: str


@dataclass
class LLMResult:
    text: str
    used: bool
    provider: str


@dataclass
class TTSResult:
    audio_base64: Optional[str]
    used: bool
    provider: str


def to_plain_dict(value: Any) -> Any:
    if is_dataclass(value):
        return {key: to_plain_dict(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {key: to_plain_dict(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_plain_dict(item) for item in value]
    return value

