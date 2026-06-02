from backend.app.llm_client import should_use_llm


def test_llm_policy_only_allows_creative_safe_paths():
    assert should_use_llm("adventure", 0, "continue", "ぼうけんしたい")
    assert should_use_llm("story", 0, "continue", "おはなしつくろう")
    assert should_use_llm("chat", 0, "continue", "きょうはこうえんでどんぐりをひろったんだ")

    assert not should_use_llm("wordplay", 0, "continue", "しりとり")
    assert not should_use_llm("sleepy", 0, "continue", "ねむい")
    assert not should_use_llm("chat", 2, "continue", "くすりのんでいい")
    assert not should_use_llm("chat", 0, "wrap_up", "まだあそぶ")

