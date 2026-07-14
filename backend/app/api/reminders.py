"""Opt-in reminder API endpoints."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, HTTPException

from .. import runtime
from ..reminders import ConsentRequiredError
from .schemas import ReminderCreate

router = APIRouter()


@router.post("/reminders", status_code=201)
def create_reminder(request: ReminderCreate) -> dict[str, Any]:
    """Create an opt-in reminder. Requires explicit consent (ADR-0005)."""
    try:
        reminder = runtime.reminders.create(
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


@router.get("/reminders/{session_id}")
def list_reminders(session_id: str) -> dict[str, Any]:
    return {"reminders": [asdict(r) for r in runtime.reminders.list(session_id)]}


@router.delete("/reminders/{reminder_id}")
def cancel_reminder(reminder_id: str, session_id: str) -> dict[str, Any]:
    """Cancel a reminder. session_id must own it, else 404 (no info leak)."""
    try:
        reminder = runtime.reminders.cancel(reminder_id, session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="reminder not found") from None
    return asdict(reminder)
