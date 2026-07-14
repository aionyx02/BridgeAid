"""Request models shared by API routers."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


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
