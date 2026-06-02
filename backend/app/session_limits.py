from __future__ import annotations

from datetime import datetime, timedelta

from .schemas import SessionDecision, SessionState, Settings


def wants_one_more(text: str) -> bool:
    normalized = (text or "").strip()
    return any(keyword in normalized for keyword in ["まだ", "もういっかい", "もう一回", "つづき", "もっと"])


def evaluate_session_limit(
    session: SessionState,
    settings: Settings,
    now: datetime,
    text: str,
    today_seconds: int,
) -> SessionDecision:
    if today_seconds >= settings.daily_limit_minutes * 60:
        session.pending_wrap_up = True
        return SessionDecision(action="end", template_key="rest_daily", reason="daily_limit")

    if session.pending_wrap_up:
        if wants_one_more(text) and not session.extended_once:
            session.extended_once = True
            session.pending_wrap_up = False
            return SessionDecision(action="extend", template_key="rest_extend", reason="single_extension")
        return SessionDecision(action="end", template_key="rest", reason="wrap_up_reached")

    started_at = datetime.fromisoformat(session.started_at)
    elapsed = now - started_at
    turn_budget = settings.max_turns + (1 if session.extended_once else 0)
    if session.turn_count >= turn_budget or elapsed >= timedelta(minutes=settings.session_limit_minutes):
        session.pending_wrap_up = True
        return SessionDecision(action="wrap_up", template_key="rest", reason="session_limit")

    return SessionDecision(action="continue", reason="within_limit")

