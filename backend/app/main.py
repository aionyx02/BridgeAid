"""BridgeAid FastAPI application.

Runs without a database or LINE secret (degraded mode, ADR-0003):
- ``GET  /healthz``       liveness + what is configured
- ``POST /recommend``     rule-engine recommendations (no DB needed)
- ``POST /chat``          conversational entry (Web): one turn per request
- ``POST /line/webhook``  signature-verified LINE events -> same conversation

Local daemon:  ``uv run uvicorn app.main:app --reload``
"""

from __future__ import annotations

import json
from dataclasses import asdict
from functools import lru_cache
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from . import config
from .conversation import ConversationManager, InMemorySessionStore
from .line.client import build_reply_client
from .line.webhook import verify_signature
from .rule_engine import evaluate_all, load_rules

app = FastAPI(title="BridgeAid", summary="Proactive Public Service Navigator")

_session_store = InMemorySessionStore()
reply_client = build_reply_client()


@lru_cache(maxsize=1)
def _rules() -> list[dict[str, Any]]:
    """Load and cache validated service rules once per process."""
    return load_rules()


@lru_cache(maxsize=1)
def _manager() -> ConversationManager:
    return ConversationManager(_rules(), _session_store)


class RecommendRequest(BaseModel):
    profile: dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted citizen profile, e.g. residence_city, event_type, age.",
    )


class ChatRequest(BaseModel):
    session_id: str = Field(description="Anonymous, caller-chosen conversation id.")
    message: str


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    settings = config.load_settings()
    return {
        "status": "ok",
        "rules_loaded": len(_rules()),
        "line_configured": settings.line_configured,
        "db_configured": settings.db_configured,
    }


@app.post("/recommend")
def recommend(request: RecommendRequest) -> dict[str, Any]:
    """Return explainable recommendations. AI never decides eligibility here."""
    results = evaluate_all(_rules(), request.profile)
    return {"results": [asdict(result) for result in results]}


@app.post("/chat")
def chat(request: ChatRequest) -> dict[str, Any]:
    """One conversation turn: ask the next field or return a recommendation."""
    reply = _manager().handle_message(request.session_id, request.message, channel="web")
    return asdict(reply)


@app.post("/line/webhook")
async def line_webhook(request: Request) -> dict[str, str]:
    settings = config.load_settings()
    if not settings.line_configured:
        raise HTTPException(status_code=503, detail="LINE webhook not configured")

    body = await request.body()
    signature = request.headers.get("X-Line-Signature")
    if not verify_signature(settings.line_channel_secret or "", body, signature):
        raise HTTPException(status_code=401, detail="invalid signature")

    payload = json.loads(body or b"{}")
    manager = _manager()
    for event in payload.get("events", []):
        if event.get("type") != "message" or event.get("message", {}).get("type") != "text":
            continue
        source = event.get("source", {})
        session_id = source.get("userId") or event.get("replyToken", "")
        reply = manager.handle_message(session_id, event["message"]["text"], channel="line")
        reply_token = event.get("replyToken")
        if settings.line_send_configured and reply_token:
            reply_client.reply(settings.line_channel_access_token or "", reply_token, reply)

    return {"status": "ok"}
