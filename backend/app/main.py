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
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import config
from .conversation import ConversationManager, InMemorySessionStore
from .line.client import build_reply_client
from .line.webhook import verify_signature
from .recommendation import build_recommendation
from .reminders import ConsentRequiredError, InMemoryReminderStore, ReminderService
from .rule_engine import evaluate_all, load_rules

app = FastAPI(title="BridgeAid", summary="Proactive Public Service Navigator")
DEMO_DIR = Path(__file__).resolve().parents[2] / "demo"
app.mount("/demo", StaticFiles(directory=DEMO_DIR, html=True), name="demo")

_session_store = InMemorySessionStore()
_reminders = ReminderService(InMemoryReminderStore())
reply_client = build_reply_client()


@lru_cache(maxsize=1)
def _rules() -> list[dict[str, Any]]:
    """Load and cache validated service rules once per process."""
    return load_rules()


@lru_cache(maxsize=1)
def _rules_by_id() -> dict[str, dict[str, Any]]:
    return {rule["id"]: rule for rule in _rules()}


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


class ReminderCreate(BaseModel):
    session_id: str
    reminder_type: str = Field(description="document | deadline | renewal | eligibility")
    scheduled_at: str = Field(description="ISO-8601 datetime")
    channel: str = "line"
    consent: bool = Field(default=False, description="Must be true (opt-in) to create.")
    note: str | None = None


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
    evaluations = evaluate_all(_rules(), request.profile)
    recommendation = build_recommendation(evaluations, _rules_by_id())
    return {
        "results": [asdict(result) for result in evaluations],
        "conflicts": recommendation.conflicts,
        "document_checklist": recommendation.document_checklist,
    }


@app.post("/chat")
def chat(request: ChatRequest) -> dict[str, Any]:
    """One conversation turn: ask the next field or return a recommendation."""
    reply = _manager().handle_message(request.session_id, request.message, channel="web")
    return asdict(reply)


@app.post("/reminders", status_code=201)
def create_reminder(request: ReminderCreate) -> dict[str, Any]:
    """Create an opt-in reminder. Requires explicit consent (ADR-0005)."""
    try:
        reminder = _reminders.create(
            request.session_id,
            request.reminder_type,
            request.scheduled_at,
            request.channel,
            consent=request.consent,
            note=request.note,
        )
    except ConsentRequiredError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return asdict(reminder)


@app.get("/reminders/{session_id}")
def list_reminders(session_id: str) -> dict[str, Any]:
    return {"reminders": [asdict(r) for r in _reminders.list(session_id)]}


@app.delete("/reminders/{reminder_id}")
def cancel_reminder(reminder_id: str, session_id: str) -> dict[str, Any]:
    """Cancel a reminder. session_id must own it, else 404 (no info leak)."""
    try:
        reminder = _reminders.cancel(reminder_id, session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="reminder not found") from None
    return asdict(reminder)


@app.get("/services")
def list_services() -> dict[str, Any]:
    """Source-trace listing: every service with its review status."""
    return {
        "services": [
            {
                "service_id": rule["id"],
                "name": rule["name"],
                "category": rule["category"],
                "status": rule.get("status", "active"),
                "needs_review": rule.get("status") == "needs_review",
            }
            for rule in _rules()
        ]
    }


@app.get("/services/{service_id}/source")
def service_source(service_id: str) -> dict[str, Any]:
    """Traceable source for one service: official url, version, last_checked_at."""
    rule = _rules_by_id().get(service_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="service not found")
    return {
        "service_id": service_id,
        "service_name": rule["name"],
        "version": rule["version"],
        "status": rule.get("status", "active"),
        "needs_review": rule.get("status") == "needs_review",
        "source": rule["source"],
    }


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
