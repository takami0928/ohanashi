from datetime import datetime, timedelta

from backend.app.schemas import SessionState, Settings
from backend.app.session_limits import evaluate_session_limit


def test_session_limit_wraps_and_allows_one_extension():
    settings = Settings(max_turns=5, session_limit_minutes=8, daily_limit_minutes=25)
    now = datetime(2026, 6, 2, 10, 0, 0)
    session = SessionState(
        session_id="s1",
        started_at=(now - timedelta(minutes=2)).isoformat(),
        turn_count=5,
    )

    wrap_up = evaluate_session_limit(session, settings, now, "まだはなす", today_seconds=0)
    assert wrap_up.action == "wrap_up"
    assert session.pending_wrap_up is True

    extend = evaluate_session_limit(session, settings, now, "まだ", today_seconds=0)
    assert extend.action == "extend"
    assert session.extended_once is True
    assert session.pending_wrap_up is False

    session.turn_count = 6
    second_wrap_up = evaluate_session_limit(session, settings, now, "つづき", today_seconds=0)
    assert second_wrap_up.action == "wrap_up"

