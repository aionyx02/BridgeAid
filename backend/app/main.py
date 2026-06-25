"""BridgeAid FastAPI application.

Runs without a database or LINE secret (degraded mode, ADR-0003):
- ``GET  /healthz``       liveness + what is configured
- ``POST /recommend``     rule-engine recommendations (no DB needed)
- ``POST /line/webhook``  signature-verified LINE events

Local daemon:  ``uv run uvicorn app.main:app --reload``
"""

from __future__ import annotations

from dataclasses import asdict
from functools import lru_cache
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from . import config
from .line.webhook import verify_signature
from .rule_engine import evaluate_all, load_rules

app = FastAPI(title="BridgeAid", summary="Proactive Public Service Navigator")


@lru_cache(maxsize=1)
def _rules() -> list[dict[str, Any]]:
    """Load and cache validated service rules once per process."""
    return load_rules()


class RecommendRequest(BaseModel):
    profile: dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted citizen profile, e.g. residence_city, event_type, age.",
    )


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


@app.post("/line/webhook")
async def line_webhook(request: Request) -> dict[str, str]:
    settings = config.load_settings()
    if not settings.line_configured:
        raise HTTPException(status_code=503, detail="LINE webhook not configured")

    body = await request.body()
    signature = request.headers.get("X-Line-Signature")
    if not verify_signature(settings.line_channel_secret or "", body, signature):
        raise HTTPException(status_code=401, detail="invalid signature")

    # Minimal skeleton: accept the delivery. Event handling lands in Week 4.
    return {"status": "ok"}
