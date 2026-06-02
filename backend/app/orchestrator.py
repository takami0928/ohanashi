from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from .asr_client import ASRClient
from .db import BaseStorage
from .llm_client import LLMClient, should_use_llm
from .memory import build_memory_updates
from .mode_classifier import classify_mode
from .safety import assess_safety, sanitize_response
from .schemas import (
    MODE_ADVENTURE,
    MODE_AMBIGUOUS,
    MODE_CHAT,
    MODE_SLEEPY,
    MODE_STORY,
    MODE_WORDPLAY,
    MemoryCard,
    SessionState,
    Settings,
    TurnRequest,
    TurnResult,
)
from .session_limits import evaluate_session_limit
from .templates import pick_template, render_mode_choice
from .tts_client import TTSClient


STATE_LABELS = {
    "listening": "きいてるよ",
    "thinking": "かんがえ中",
    "speaking": "おはなしするよ",
    "resting": "ちょっと休憩",
}


class Orchestrator:
    def __init__(self, storage: BaseStorage, llm_client: LLMClient, asr_client: ASRClient, tts_client: TTSClient) -> None:
        self.storage = storage
        self.llm_client = llm_client
        self.asr_client = asr_client
        self.tts_client = tts_client
        self.sessions: Dict[str, SessionState] = {}

    def process_turn(self, request: TurnRequest) -> TurnResult:
        settings = self.storage.get_settings()
        now = datetime.now()
        session = self._get_or_create_session(request.session_id, now.isoformat())

        asr_result = self.asr_client.transcribe(request.audio_base64, request.text_input)
        transcript = (asr_result.text or "").strip()
        if not asr_result.success or not transcript:
            session.failure_count += 1
            response_text = pick_template(
                f"asr_retry_{min(session.failure_count, 3)}",
                session.turn_count,
            )
            return self._build_result(
                session=session,
                mode=session.last_mode,
                safety_level=0,
                response_text=response_text,
                settings=settings,
                transcript=transcript,
                request=request,
                used_llm=False,
                used_asr=asr_result.success,
                state_label=STATE_LABELS["speaking"],
                debug_extra={"responsePath": "template", "sessionAction": "asr_retry"},
            )

        session.failure_count = 0
        safety = assess_safety(transcript)
        today = now.date().isoformat()
        usage_before = self.storage.get_usage_summary(today, days=7)
        session_decision = evaluate_session_limit(
            session=session,
            settings=settings,
            now=now,
            text=transcript,
            today_seconds=int(usage_before["todaySeconds"]),
        )

        if session_decision.action in {"wrap_up", "end", "extend"}:
            response_text = pick_template(session_decision.template_key or "rest", session.turn_count)
            if session_decision.action == "extend":
                session.turn_count += 1
            self.storage.record_usage(today, request.recording_seconds, session.last_mode)
            return self._build_result(
                session=session,
                mode=session.last_mode,
                safety_level=safety.level,
                response_text=response_text,
                settings=settings,
                transcript=transcript,
                request=request,
                used_llm=False,
                used_asr=True,
                state_label=STATE_LABELS["resting"],
                debug_extra={"responsePath": "template", "sessionAction": session_decision.action},
            )

        if safety.level > 0:
            response_text = pick_template(safety.template_key, session.turn_count)
            response_text = sanitize_response(response_text, pick_template("safe_level_2"))
            session.turn_count += 1
            session.last_mode = MODE_CHAT
            self.storage.record_usage(today, request.recording_seconds, MODE_CHAT)
            return self._build_result(
                session=session,
                mode=MODE_CHAT,
                safety_level=safety.level,
                response_text=response_text,
                settings=settings,
                transcript=transcript,
                request=request,
                used_llm=False,
                used_asr=True,
                state_label=STATE_LABELS["speaking"],
                debug_extra={"responsePath": "template", "sessionAction": "safety"},
            )

        mode_decision = classify_mode(transcript, settings.enabled_modes())
        memories = self.storage.list_memories(now.isoformat())
        memory_context = _memory_context(memories, settings)

        if mode_decision.mode == MODE_AMBIGUOUS:
            response_text = render_mode_choice(mode_decision.choices)
            response_path = "template"
            used_llm = False
            mode = MODE_CHAT
        else:
            mode = mode_decision.mode
            response_path = "rule"
            fallback = self._generate_rule_response(mode, transcript, memory_context, settings, session.turn_count)
            response_text = fallback
            llm_provider = "not-requested"
            if should_use_llm(mode, safety.level, "continue", transcript):
                llm_result = self.llm_client.generate(mode, transcript, memory_context, fallback)
                response_text = llm_result.text
                used_llm = llm_result.used
                llm_provider = llm_result.provider
                response_path = "llm" if llm_result.used else "rule"
            else:
                used_llm = False

        fallback_text = self._generate_rule_response(mode, transcript, memory_context, settings, session.turn_count)
        response_text = sanitize_response(response_text, fallback_text)

        updates = build_memory_updates(transcript, mode, safety, now)
        for card in updates:
            self.storage.upsert_memory(card)

        session.turn_count += 1
        session.last_mode = mode
        self.storage.record_usage(today, request.recording_seconds, mode)
        return self._build_result(
            session=session,
            mode=mode,
            safety_level=safety.level,
            response_text=response_text,
            settings=settings,
            transcript=transcript,
            request=request,
            used_llm=used_llm,
            used_asr=True,
            state_label=STATE_LABELS["speaking"],
            debug_extra={
                "responsePath": response_path,
                "sessionAction": "continue",
                "llmProvider": llm_provider,
                "memoryUpdates": [card.key for card in updates],
            },
        )

    def get_dashboard_payload(self) -> Dict[str, object]:
        settings = self.storage.get_settings()
        today = datetime.now().date().isoformat()
        usage = self.storage.get_usage_summary(today, days=7)
        memories = [card.__dict__ for card in self.storage.list_memories(datetime.now().isoformat())]
        return {
            "settings": settings.__dict__,
            "usage": usage,
            "memories": memories,
            "storageDriver": self.storage.driver,
        }

    def update_settings(self, payload: Dict[str, object]) -> Dict[str, object]:
        updated = self.storage.save_settings(payload)
        return updated.__dict__

    def update_memory(self, card_id: str, payload: Dict[str, object]) -> Dict[str, object]:
        existing_cards = {card.id: card for card in self.storage.list_memories(datetime.now().isoformat())}
        existing = existing_cards.get(card_id)
        if existing is None:
            raise KeyError(card_id)
        updated = MemoryCard(
            id=existing.id,
            category=str(payload.get("category", existing.category)),
            key=str(payload.get("key", existing.key)),
            value=str(payload.get("value", existing.value)),
            scope=str(payload.get("scope", existing.scope)),
            created_at=existing.created_at,
            updated_at=datetime.now().isoformat(),
            expires_at=payload.get("expires_at", existing.expires_at),
        )
        self.storage.upsert_memory(updated)
        return updated.__dict__

    def delete_memory(self, card_id: str) -> None:
        self.storage.delete_memory(card_id)

    def _build_result(
        self,
        session: SessionState,
        mode: str,
        safety_level: int,
        response_text: str,
        settings: Settings,
        transcript: str,
        request: TurnRequest,
        used_llm: bool,
        used_asr: bool,
        state_label: str,
        debug_extra: Dict[str, object],
    ) -> TurnResult:
        tts_result = self.tts_client.synthesize(response_text, settings)
        debug_payload = None
        if request.debug or settings.debug_mode:
            debug_payload = {
                "transcript": transcript,
                "responseText": response_text,
                "session": session.__dict__,
                **debug_extra,
            }
        return TurnResult(
            session_id=session.session_id,
            mode=mode,
            safety_level=safety_level,
            state_label=state_label,
            response_text=response_text,
            audio_base64=tts_result.audio_base64,
            used_llm=used_llm,
            used_asr=used_asr,
            used_tts=tts_result.used,
            debug=debug_payload,
        )

    def _get_or_create_session(self, session_id: str, started_at: str) -> SessionState:
        session = self.sessions.get(session_id)
        if session is None:
            session = SessionState(session_id=session_id, started_at=started_at)
            self.sessions[session_id] = session
        return session

    def _generate_rule_response(
        self,
        mode: str,
        transcript: str,
        memory_context: Dict[str, str],
        settings: Settings,
        turn_seed: int,
    ) -> str:
        if _is_dependency_statement(transcript):
            return pick_template("dependency", turn_seed)

        if mode == MODE_WORDPLAY:
            if "しりとり" in transcript:
                return pick_template("wordplay_shiritori", turn_seed)
            if "なぞなぞ" in transcript:
                return pick_template("wordplay_riddle", turn_seed)
            return pick_template("wordplay_general", turn_seed)

        if mode == MODE_SLEEPY:
            return pick_template("sleepy", turn_seed)

        if mode == MODE_ADVENTURE:
            if "宇宙" in transcript:
                return pick_template("adventure_start_space", turn_seed)
            if "お店屋さん" in transcript or "おみせやさん" in transcript:
                return pick_template("adventure_start_shop", turn_seed)
            if "恐竜" in transcript:
                return "きょうりゅうのしまについたよ。大きな足あとがあるよ。見る？かくれる？"
            return pick_template("adventure_start_forest", turn_seed)

        if mode == MODE_STORY:
            favorite = memory_context.get("favorite_thing") or "ちいさなほし"
            return f"むかしむかし、{favorite}がぴかっとひかったよ。森にいく？空にいく？"

        if _is_greeting(transcript):
            child_name = settings.child_name or memory_context.get("child_name") or ""
            if child_name:
                return f"こんにちは、{child_name}。今日はなにしてあそぶ？"
            return "こんにちは。今日はなにしてあそぶ？"

        if "ありがとう" in transcript:
            return "えへへ。どういたしまして。"

        favorite = memory_context.get("favorite_thing")
        if favorite:
            return f"{favorite}の話、また聞きたいな。今日はどんな感じ？"
        return pick_template("teach_me" if turn_seed % 2 else "hear_back", turn_seed)


def _memory_context(memories: List[MemoryCard], settings: Settings) -> Dict[str, str]:
    context: Dict[str, str] = {
        "toy_name": settings.toy_name,
        "child_name": settings.child_name,
    }
    for card in memories:
        context[card.key] = card.value
    return context


def _is_greeting(text: str) -> bool:
    return any(keyword in text for keyword in ["こんにちは", "おはよう", "やあ", "こんばんは"])


def _is_dependency_statement(text: str) -> bool:
    return any(keyword in text for keyword in ["いちばんのともだち", "ずっといっしょ", "ぼくだけ", "あなただけ"])
