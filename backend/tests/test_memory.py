from datetime import datetime

from backend.app.memory import build_memory_updates, is_memory_safe_to_store
from backend.app.safety import assess_safety


def test_memory_updates_store_safe_abstract_cards_only():
    now = datetime(2026, 6, 2, 10, 0, 0)
    safety = assess_safety("きょうりゅうがすき")
    cards = build_memory_updates("きょうりゅうがすき", "chat", safety, now)
    values = {card.key: card.value for card in cards}

    assert is_memory_safe_to_store("きょうりゅうがすき", safety)
    assert values["favorite_thing"] == "きょうりゅう"
    assert values["recent_topic"] == "きょうりゅうが好き"


def test_memory_updates_skip_sensitive_content():
    now = datetime(2026, 6, 2, 10, 0, 0)
    safety = assess_safety("くすりのんでいい")
    cards = build_memory_updates("くすりのんでいい", "chat", safety, now)
    assert not is_memory_safe_to_store("くすりのんでいい", safety)
    assert cards == []

