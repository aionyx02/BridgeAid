"""Conversational web entrypoint."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter

from .. import runtime
from .schemas import ChatRequest

router = APIRouter()


@router.post("/chat")
def chat(request: ChatRequest) -> dict[str, Any]:
    """One conversation turn: ask the next field or return a recommendation."""
    reply = runtime.manager().handle_message(request.session_id, request.message, channel="web")
    return asdict(reply)
