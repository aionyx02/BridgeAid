"""Opt-in reminder system (ADR-0005).

Reminders are created only with explicit consent and store minimized fields
(session id, type, time, channel, status) — no names or free-text narrative
(docs/security.md). Storage is in-memory behind a `ReminderStore` port; the DB
table `reminder_tasks` and actual delivery (scheduling) come later.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

REMINDER_TYPES = frozenset({"document", "deadline", "renewal", "eligibility"})
CHANNELS = frozenset({"line", "email"})

STATUS_PENDING = "pending"
STATUS_CANCELLED = "cancelled"
STATUS_SENT = "sent"


class ConsentRequiredError(PermissionError):
    """Raised when a reminder is created without explicit opt-in consent."""


@dataclass
class Reminder:
    id: str
    session_id: str
    reminder_type: str
    scheduled_at: str
    channel: str
    status: str = STATUS_PENDING
    note: str | None = None


class ReminderStore(Protocol):
    def add(self, reminder: Reminder) -> None: ...
    def get(self, reminder_id: str) -> Reminder | None: ...
    def list_for(self, session_id: str) -> list[Reminder]: ...
    def list_pending(self) -> list[Reminder]: ...
    def save(self, reminder: Reminder) -> None: ...


class InMemoryReminderStore:
    """Process-local store. Swap for a `reminder_tasks`-backed store later."""

    def __init__(self) -> None:
        self._reminders: dict[str, Reminder] = {}

    def add(self, reminder: Reminder) -> None:
        self._reminders[reminder.id] = reminder

    def get(self, reminder_id: str) -> Reminder | None:
        return self._reminders.get(reminder_id)

    def list_for(self, session_id: str) -> list[Reminder]:
        return [r for r in self._reminders.values() if r.session_id == session_id]

    def list_pending(self) -> list[Reminder]:
        return [r for r in self._reminders.values() if r.status == STATUS_PENDING]

    def save(self, reminder: Reminder) -> None:
        self._reminders[reminder.id] = reminder


class ReminderService:
    def __init__(self, store: ReminderStore) -> None:
        self._store = store

    def create(
        self,
        session_id: str,
        reminder_type: str,
        scheduled_at: str,
        channel: str = "line",
        *,
        consent: bool,
        note: str | None = None,
    ) -> Reminder:
        if not consent:
            raise ConsentRequiredError("opt-in consent is required to create a reminder")
        if not session_id:
            raise ValueError("session_id is required")
        if reminder_type not in REMINDER_TYPES:
            raise ValueError(f"unsupported reminder_type: {reminder_type!r}")
        if channel not in CHANNELS:
            raise ValueError(f"unsupported channel: {channel!r}")
        self._validate_datetime(scheduled_at)

        reminder = Reminder(
            id=uuid.uuid4().hex,
            session_id=session_id,
            reminder_type=reminder_type,
            scheduled_at=scheduled_at,
            channel=channel,
            note=note,
        )
        self._store.add(reminder)
        return reminder

    def list(self, session_id: str) -> list[Reminder]:
        return self._store.list_for(session_id)

    def cancel(self, reminder_id: str, session_id: str) -> Reminder:
        reminder = self._store.get(reminder_id)
        if reminder is None or reminder.session_id != session_id:
            # Do not reveal existence of another session's reminder.
            raise KeyError(reminder_id)
        reminder.status = STATUS_CANCELLED
        self._store.save(reminder)
        return reminder

    @staticmethod
    def _validate_datetime(value: str) -> None:
        try:
            datetime.fromisoformat(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"scheduled_at must be ISO-8601 datetime: {value!r}") from exc
