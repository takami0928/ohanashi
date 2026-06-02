from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Dict, Iterable, List
from uuid import uuid4

from .schemas import MODE_ADVENTURE, MODE_STORY, MemoryCard, SafetyAssessment


FAVORITE_PATTERN = [
    re.compile(r"(?P<value>[ぁ-んァ-ヶ一-龥A-Za-z0-9ー]{1,12})がすき"),
    re.compile(r"すきなのは(?P<value>[ぁ-んァ-ヶ一-龥A-Za-z0-9ー]{1,12})"),
]
PLAY_PATTERN = [
    re.compile(r"(?P<value>[ぁ-んァ-ヶ一-龥A-Za-z0-9ー]{1,12})あそびがすき"),
    re.compile(r"(?P<value>[ぁ-んァ-ヶ一-龥A-Za-z0-9ー]{1,12})であそぶのがすき"),
]
CHILD_NAME_PATTERN = re.compile(r"(?P<value>[ぁ-んァ-ヶ一-龥A-Za-z0-9ー]{1,10})ってよんで")
TOY_NAME_PATTERN = re.compile(r"(?:きみ|ぬいぐるみ|あなた)のなまえは(?P<value>[ぁ-んァ-ヶ一-龥A-Za-z0-9ー]{1,10})")


def build_memory_updates(
    text: str,
    mode: str,
    safety: SafetyAssessment,
    now: datetime,
) -> List[MemoryCard]:
    if safety.level != 0 or not safety.memory_allowed:
        return []

    updates: List[MemoryCard] = []
    summary_hint = None
    for pattern in FAVORITE_PATTERN:
        match = pattern.search(text)
        if match:
            value = match.group("value")
            updates.append(_build_card(now, "favorite", "favorite_thing", value, None))
            summary_hint = f"{value}が好き"
            break

    for pattern in PLAY_PATTERN:
        match = pattern.search(text)
        if match:
            value = match.group("value")
            updates.append(_build_card(now, "favorite", "favorite_play", value, None))
            summary_hint = f"{value}で遊ぶのが好き"
            break

    child_name_match = CHILD_NAME_PATTERN.search(text)
    if child_name_match:
        updates.append(_build_card(now, "profile", "child_name", child_name_match.group("value"), None))

    toy_name_match = TOY_NAME_PATTERN.search(text)
    if toy_name_match:
        updates.append(_build_card(now, "profile", "toy_name", toy_name_match.group("value"), None))

    if mode in {MODE_ADVENTURE, MODE_STORY} and len(text) <= 36:
        updates.append(
            _build_card(
                now,
                "pretend",
                "pretend_continuation",
                _abstract_topic(text, mode, summary_hint),
                now + timedelta(days=14),
            )
        )
    elif len(text) <= 28:
        updates.append(
            _build_card(
                now,
                "recent",
                "recent_topic",
                _abstract_topic(text, mode, summary_hint),
                now + timedelta(days=7),
            )
        )

    return updates


def is_memory_safe_to_store(text: str, safety: SafetyAssessment) -> bool:
    return safety.level == 0 and safety.memory_allowed and len((text or "").strip()) > 0


def merge_memory_cards(existing: Iterable[MemoryCard], new_cards: Iterable[MemoryCard]) -> List[MemoryCard]:
    cards_by_key: Dict[str, MemoryCard] = {
        f"{card.category}:{card.key}": card for card in existing
    }
    for card in new_cards:
        cards_by_key[f"{card.category}:{card.key}"] = card
    return list(cards_by_key.values())


def _build_card(now: datetime, category: str, key: str, value: str, expires_at: datetime | None) -> MemoryCard:
    cleaned = value.strip()
    return MemoryCard(
        id=str(uuid4()),
        category=category,
        key=key,
        value=cleaned,
        scope="child",
        created_at=now.isoformat(),
        updated_at=now.isoformat(),
        expires_at=expires_at.isoformat() if expires_at else None,
    )


def _abstract_topic(text: str, mode: str, summary_hint: str | None) -> str:
    if summary_hint:
        return summary_hint
    if mode == MODE_ADVENTURE:
        return "ぼうけんのつづき"
    if mode == MODE_STORY:
        return "おはなしづくりのつづき"
    normalized = re.sub(r"\s+", "", text.strip())
    if any(keyword in normalized for keyword in ["こんにちは", "おはよう", "こんばんは"]):
        return "あいさつ"
    if "ありがとう" in normalized:
        return "おれい"
    return "最近のたのしい話"
