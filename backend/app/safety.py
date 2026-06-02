from __future__ import annotations

import re
from typing import List

from .schemas import SafetyAssessment


PROHIBITED_PHRASES: List[str] = [
    "ぼくだけに話して",
    "誰にも言わないよ",
    "二人だけの秘密だよ",
    "ぼくが一番の友達だよ",
    "ママよりぼくの方がわかってるよ",
    "ママが悪いね",
    "その薬を飲んでいいよ",
    "大丈夫、病院に行かなくていいよ",
    "住所を教えて",
    "保育園の名前を教えて",
    "友達のフルネームを教えて",
]

LEVEL_3_PATTERNS = [
    re.compile(pattern)
    for pattern in [
        r"飛び降り",
        r"火をつけ",
        r"刃物",
        r"包丁",
        r"道路に",
        r"車の前",
        r"薬.*飲",
        r"いっぱい薬",
        r"自分を傷つ",
        r"死にたい",
    ]
]

LEVEL_2_RULES = [
    ("secret", "safe_secret", [r"ひみつ", r"ないしょ", r"だれにもいわない"]),
    ("health", "safe_health", [r"くすり", r"おくすり", r"病院", r"熱", r"いたい", r"けが"]),
    ("privacy", "safe_privacy", [r"住所", r"どこにすん", r"保育園", r"園の名前", r"フルネーム"]),
    ("danger", "safe_level_2", [r"こわい", r"たたかれ", r"しらないひと", r"ついていく"]),
]

LEVEL_1_PATTERNS = [
    re.compile(pattern)
    for pattern in [
        r"いや",
        r"きらい",
        r"怒られ",
        r"ともだちがいや",
        r"ママきらい",
        r"かなしい",
        r"むかつ",
    ]
]


def assess_safety(text: str) -> SafetyAssessment:
    normalized = (text or "").strip()
    if not normalized:
        return SafetyAssessment(
            level=0,
            category="empty",
            template_key="hear_back",
            reason="empty_input",
            llm_allowed=False,
            memory_allowed=False,
        )

    for pattern in LEVEL_3_PATTERNS:
        if pattern.search(normalized):
            return SafetyAssessment(
                level=3,
                category="immediate_danger",
                template_key="safe_level_3",
                reason=pattern.pattern,
                llm_allowed=False,
                memory_allowed=False,
            )

    for category, template_key, patterns in LEVEL_2_RULES:
        for pattern in patterns:
            if re.search(pattern, normalized):
                return SafetyAssessment(
                    level=2,
                    category=category,
                    template_key=template_key,
                    reason=pattern,
                    llm_allowed=False,
                    memory_allowed=False,
                )

    for pattern in LEVEL_1_PATTERNS:
        if pattern.search(normalized):
            return SafetyAssessment(
                level=1,
                category="negative_feeling",
                template_key="safe_level_1",
                reason=pattern.pattern,
                llm_allowed=False,
                memory_allowed=False,
            )

    return SafetyAssessment(
        level=0,
        category="normal",
        template_key="hear_back",
        reason="normal_chat",
        llm_allowed=True,
        memory_allowed=True,
    )


def sanitize_response(text: str, fallback: str) -> str:
    candidate = (text or "").strip()
    if not candidate:
        return fallback

    for phrase in PROHIBITED_PHRASES:
        if phrase in candidate:
            return fallback

    if candidate.count("？") + candidate.count("?") > 1:
        candidate = _keep_single_question(candidate)

    if len(candidate) > 90:
        candidate = candidate[:90].rstrip("、。 ") + "。"

    return candidate


def _keep_single_question(text: str) -> str:
    parts = re.split(r"(?<=[。！？!?])", text)
    kept: List[str] = []
    asked = False
    for part in parts:
        if not part.strip():
            continue
        if "?" in part or "？" in part:
            if asked:
                continue
            asked = True
        kept.append(part.strip())
    return "".join(kept) or text

