from __future__ import annotations

from typing import Dict, List

from .schemas import MODE_ADVENTURE, MODE_AMBIGUOUS, MODE_CHAT, MODE_SLEEPY, MODE_STORY, MODE_WORDPLAY, ModeDecision


MODE_KEYWORDS: Dict[str, List[str]] = {
    MODE_WORDPLAY: ["しりとり", "なぞなぞ", "ことば"],
    MODE_ADVENTURE: ["冒険", "ぼうけん", "探検", "恐竜の島", "宇宙", "お店屋さん", "おみせやさん"],
    MODE_STORY: ["お話つくろう", "おはなしつくろう", "物語", "昔々", "むかしむかし"],
    MODE_SLEEPY: ["眠い", "ねむい", "寝る", "ねる", "おやすみ"],
}

MODE_JA = {
    MODE_CHAT: "おしゃべり",
    MODE_ADVENTURE: "ぼうけん",
    MODE_WORDPLAY: "ことばあそび",
    MODE_STORY: "おはなし",
    MODE_SLEEPY: "ねむねむ",
}


def classify_mode(text: str, enabled_modes: List[str]) -> ModeDecision:
    normalized = (text or "").strip()
    matches: List[str] = []
    for mode, keywords in MODE_KEYWORDS.items():
        if mode not in enabled_modes:
            continue
        if any(keyword in normalized for keyword in keywords):
            matches.append(mode)

    if len(matches) > 1:
        mode_names = [MODE_JA[mode] for mode in matches[:2]]
        return ModeDecision(
            mode=MODE_AMBIGUOUS,
            confidence="low",
            choices=mode_names,
            reason="multiple_keyword_hits",
        )

    if len(matches) == 1:
        return ModeDecision(
            mode=matches[0],
            confidence="high",
            reason="keyword_hit",
        )

    if MODE_CHAT in enabled_modes:
        return ModeDecision(
            mode=MODE_CHAT,
            confidence="medium",
            reason="default_chat",
        )

    fallback = enabled_modes[0] if enabled_modes else MODE_CHAT
    return ModeDecision(mode=fallback, confidence="low", reason="first_enabled_mode")

