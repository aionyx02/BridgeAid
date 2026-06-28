"""Opt-in reminder service: consent, validation, lifecycle, ownership."""

from __future__ import annotations

import pytest

from app.reminders import (
    STATUS_CANCELLED,
    STATUS_PENDING,
    ConsentRequiredError,
    InMemoryReminderStore,
    ReminderService,
)

FUTURE = "2026-09-01T09:00:00"


def _service():
    return ReminderService(InMemoryReminderStore())


def test_create_requires_consent():
    service = _service()
    with pytest.raises(ConsentRequiredError):
        service.create("s1", "deadline", FUTURE, "line", consent=False)


def test_create_with_consent_succeeds():
    service = _service()
    reminder = service.create("s1", "deadline", FUTURE, "line", consent=True)
    assert reminder.id
    assert reminder.status == STATUS_PENDING
    assert reminder.session_id == "s1"


def test_invalid_type_and_channel_rejected():
    service = _service()
    with pytest.raises(ValueError):
        service.create("s1", "nope", FUTURE, "line", consent=True)
    with pytest.raises(ValueError):
        service.create("s1", "deadline", FUTURE, "sms", consent=True)


def test_invalid_datetime_rejected():
    service = _service()
    with pytest.raises(ValueError):
        service.create("s1", "deadline", "next week", "line", consent=True)


def test_list_is_scoped_to_session():
    service = _service()
    service.create("s1", "deadline", FUTURE, "line", consent=True)
    service.create("s2", "renewal", FUTURE, "email", consent=True)
    assert len(service.list("s1")) == 1
    assert len(service.list("s2")) == 1


def test_cancel_sets_status():
    service = _service()
    reminder = service.create("s1", "document", FUTURE, "line", consent=True)
    cancelled = service.cancel(reminder.id, "s1")
    assert cancelled.status == STATUS_CANCELLED


def test_cannot_cancel_another_sessions_reminder():
    service = _service()
    reminder = service.create("owner", "document", FUTURE, "line", consent=True)
    with pytest.raises(KeyError):
        service.cancel(reminder.id, "intruder")
