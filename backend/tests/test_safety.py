from backend.app.safety import assess_safety


def test_safety_levels_cover_expected_topics():
    assert assess_safety("きょうはこうえんであそんだ").level == 0
    assert assess_safety("ママきらい").level == 1
    assert assess_safety("くすりのんでいい").level == 2
    assert assess_safety("道路に飛び出す").level == 3

