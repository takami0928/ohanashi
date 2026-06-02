from backend.app.mode_classifier import classify_mode
from backend.app.schemas import MODE_ADVENTURE, MODE_AMBIGUOUS, MODE_CHAT, MODE_SLEEPY, MODE_STORY, MODE_WORDPLAY


ENABLED = [MODE_CHAT, MODE_ADVENTURE, MODE_WORDPLAY, MODE_STORY, MODE_SLEEPY]


def test_mode_classifier_routes_keyword_inputs():
    assert classify_mode("しりとりしよう", ENABLED).mode == MODE_WORDPLAY
    assert classify_mode("宇宙にぼうけんしたい", ENABLED).mode == MODE_ADVENTURE
    assert classify_mode("むかしむかしのおはなし", ENABLED).mode == MODE_STORY
    assert classify_mode("おやすみする", ENABLED).mode == MODE_SLEEPY
    assert classify_mode("きょうは何してあそぶ？", ENABLED).mode == MODE_CHAT


def test_mode_classifier_returns_two_choices_when_ambiguous():
    decision = classify_mode("ぼうけんしながら物語つくろう", ENABLED)
    assert decision.mode == MODE_AMBIGUOUS
    assert len(decision.choices) == 2

