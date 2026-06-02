from pathlib import Path

from backend.app.asr_client import ASRClient
from backend.app.db import create_storage
from backend.app.llm_client import LLMClient
from backend.app.orchestrator import Orchestrator
from backend.app.schemas import TurnRequest
from backend.app.tts_client import TTSClient


def test_storage_does_not_persist_full_transcript(tmp_path: Path):
    storage = create_storage(tmp_path, force_json=True)
    orchestrator = Orchestrator(storage=storage, llm_client=LLMClient(), asr_client=ASRClient(), tts_client=TTSClient())
    transcript = "きょうりゅうがすき"

    result = orchestrator.process_turn(
        TurnRequest(
            session_id="session-1",
            text_input=transcript,
            recording_seconds=18,
            debug=True,
        )
    )

    raw = (tmp_path / "toy_brain_state.json").read_text(encoding="utf-8")
    assert transcript not in raw
    assert "favorite_thing" in raw
    assert result.debug is not None
    assert result.debug["transcript"] == transcript
