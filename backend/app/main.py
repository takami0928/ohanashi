from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Dict, Tuple
from wsgiref.simple_server import make_server

from .asr_client import ASRClient
from .db import create_storage
from .llm_client import LLMClient
from .orchestrator import Orchestrator
from .schemas import TurnRequest, to_plain_dict
from .tts_client import TTSClient

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
storage = create_storage(DATA_DIR)
orchestrator = Orchestrator(storage=storage, llm_client=LLMClient(), asr_client=ASRClient(), tts_client=TTSClient())


def build_app():
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.middleware.cors import CORSMiddleware

        app = FastAPI(title="Local Plush Brain MVP")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @app.get("/api/health")
        def health() -> Dict[str, Any]:
            return {"ok": True, "storageDriver": storage.driver}

        @app.get("/api/bootstrap")
        def bootstrap() -> Dict[str, Any]:
            return orchestrator.get_dashboard_payload()

        @app.post("/api/child/turn")
        def child_turn(payload: Dict[str, Any]) -> Dict[str, Any]:
            return _turn_payload(payload, debug=False)

        @app.post("/api/dev/turn")
        def dev_turn(payload: Dict[str, Any]) -> Dict[str, Any]:
            return _turn_payload(payload, debug=True)

        @app.post("/api/settings")
        def settings(payload: Dict[str, Any]) -> Dict[str, Any]:
            return orchestrator.update_settings(payload)

        @app.put("/api/memories/{card_id}")
        def update_memory(card_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                return orchestrator.update_memory(card_id, payload)
            except KeyError as exc:
                raise HTTPException(status_code=404, detail=str(exc))

        @app.delete("/api/memories/{card_id}")
        def delete_memory(card_id: str) -> Dict[str, Any]:
            orchestrator.delete_memory(card_id)
            return {"ok": True}

        return app
    except Exception:
        return FallbackApiApp()


class FallbackApiApp:
    def __call__(self, environ, start_response):
        method = environ.get("REQUEST_METHOD", "GET").upper()
        path = environ.get("PATH_INFO", "")
        if method == "OPTIONS":
            return _json_response(start_response, 204, {})

        try:
            if method == "GET" and path == "/api/health":
                return _json_response(start_response, 200, {"ok": True, "storageDriver": storage.driver})
            if method == "GET" and path == "/api/bootstrap":
                return _json_response(start_response, 200, orchestrator.get_dashboard_payload())
            if method == "POST" and path == "/api/child/turn":
                payload = _read_json_body(environ)
                return _json_response(start_response, 200, _turn_payload(payload, debug=False))
            if method == "POST" and path == "/api/dev/turn":
                payload = _read_json_body(environ)
                return _json_response(start_response, 200, _turn_payload(payload, debug=True))
            if method == "POST" and path == "/api/settings":
                payload = _read_json_body(environ)
                return _json_response(start_response, 200, orchestrator.update_settings(payload))

            memory_match = re.fullmatch(r"/api/memories/([^/]+)", path)
            if memory_match and method == "PUT":
                payload = _read_json_body(environ)
                return _json_response(start_response, 200, orchestrator.update_memory(memory_match.group(1), payload))
            if memory_match and method == "DELETE":
                orchestrator.delete_memory(memory_match.group(1))
                return _json_response(start_response, 200, {"ok": True})
        except KeyError:
            return _json_response(start_response, 404, {"detail": "memory_not_found"})
        except Exception as exc:
            return _json_response(start_response, 500, {"detail": str(exc)})

        return _json_response(start_response, 404, {"detail": "not_found"})


app = build_app()


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    with make_server(host, port, app) as server:
        print(f"Serving plush brain on http://{host}:{port}")
        server.serve_forever()


def _turn_payload(payload: Dict[str, Any], debug: bool) -> Dict[str, Any]:
    request = TurnRequest(
        session_id=str(payload.get("sessionId") or "default-session"),
        audio_base64=payload.get("audioBase64"),
        text_input=payload.get("textInput"),
        recording_seconds=int(payload.get("recordingSeconds") or 20),
        debug=debug or bool(payload.get("debug")),
    )
    result = orchestrator.process_turn(request)
    return to_plain_dict(result)


def _read_json_body(environ) -> Dict[str, Any]:
    content_length = int(environ.get("CONTENT_LENGTH") or 0)
    raw_body = environ["wsgi.input"].read(content_length) if content_length else b"{}"
    if not raw_body:
        return {}
    return json.loads(raw_body.decode("utf-8"))


def _json_response(start_response: Callable[..., Any], status_code: int, payload: Dict[str, Any]):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    status_text = {
        200: "200 OK",
        204: "204 No Content",
        404: "404 Not Found",
        500: "500 Internal Server Error",
    }.get(status_code, f"{status_code} OK")
    headers = [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(body))),
        ("Access-Control-Allow-Origin", "*"),
        ("Access-Control-Allow-Headers", "Content-Type"),
        ("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS"),
    ]
    start_response(status_text, headers)
    return [body]


if __name__ == "__main__":
    serve()
