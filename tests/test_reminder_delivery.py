"""Reminder delivery scheduler (ADR-0006): due sweep, retry, LINE/simulated send."""

from __future__ import annotations

from datetime import datetime

from app import reminder_delivery
from app.config import Settings
from app.reminder_delivery import LineOrLogSender, deliver_due, reminder_text
from app.reminders import (
    STATUS_PENDING,
    STATUS_SENT,
    InMemoryReminderStore,
    Reminder,
    ReminderService,
)

NOW = datetime(2026, 7, 2, 12, 0, 0)


class RecordingSender:
    def __init__(self) -> None:
        self.sent: list[Reminder] = []

    def send(self, reminder: Reminder) -> None:
        self.sent.append(reminder)


class FailingSender:
    def send(self, reminder: Reminder) -> None:
        raise RuntimeError("LINE down")


def _store_with(*reminders: Reminder) -> InMemoryReminderStore:
    store = InMemoryReminderStore()
    for reminder in reminders:
        store.add(reminder)
    return store


def _reminder(reminder_id: str, scheduled_at: str, **overrides) -> Reminder:
    values = dict(
        id=reminder_id,
        session_id="sess-1",
        reminder_type="deadline",
        scheduled_at=scheduled_at,
        channel="line",
    )
    values.update(overrides)
    return Reminder(**values)


def test_due_pending_reminder_is_sent_and_marked():
    store = _store_with(_reminder("r1", "2026-07-02T11:59:00"))
    sender = RecordingSender()
    assert deliver_due(store, sender, now=NOW) == 1
    assert sender.sent[0].id == "r1"
    assert store.get("r1").status == STATUS_SENT


def test_future_reminder_stays_pending():
    store = _store_with(_reminder("r1", "2026-07-02T12:01:00"))
    sender = RecordingSender()
    assert deliver_due(store, sender, now=NOW) == 0
    assert sender.sent == []
    assert store.get("r1").status == STATUS_PENDING


def test_cancelled_reminder_is_not_delivered():
    store = _store_with(_reminder("r1", "2026-07-02T11:00:00", status="cancelled"))
    assert deliver_due(store, RecordingSender(), now=NOW) == 0


def test_failed_send_stays_pending_and_others_still_deliver():
    store = _store_with(
        _reminder("r1", "2026-07-02T11:00:00"),
        _reminder("r2", "2026-07-02T11:00:00"),
    )

    class FailFirst:
        def send(self, reminder: Reminder) -> None:
            if reminder.id == "r1":
                raise RuntimeError("LINE down")

    assert deliver_due(store, FailFirst(), now=NOW) == 1
    assert store.get("r1").status == STATUS_PENDING  # retried next tick
    assert store.get("r2").status == STATUS_SENT


def test_timezone_aware_scheduled_at_is_handled():
    store = _store_with(_reminder("r1", "2026-07-02T00:00:00+00:00"))
    # Any local NOW on 2026-07-03 is safely past midnight UTC of the 2nd.
    assert deliver_due(store, RecordingSender(), now=datetime(2026, 7, 3, 12, 0, 0)) == 1


def test_service_created_reminder_flows_through_delivery():
    store = InMemoryReminderStore()
    service = ReminderService(store)
    service.create("sess-9", "document", "2026-07-01T09:00:00", "line", consent=True)
    sender = RecordingSender()
    assert deliver_due(store, sender, now=NOW) == 1
    assert sender.sent[0].session_id == "sess-9"


def test_reminder_text_uses_template_note_and_disclaimer():
    text = reminder_text(_reminder("r1", "2026-07-02T11:00:00", note="低收入戶證明"))
    assert "申請期限" in text
    assert "低收入戶證明" in text
    assert "承辦單位" in text


def _settings(token: str | None) -> Settings:
    return Settings(
        line_channel_id=None,
        line_channel_secret=None,
        line_channel_access_token=token,
        database_url=None,
    )


def test_sender_pushes_via_line_when_configured(monkeypatch):
    pushes: list[tuple[str, str, str]] = []
    monkeypatch.setattr(reminder_delivery.config, "load_settings", lambda: _settings("token-1"))
    monkeypatch.setattr(
        reminder_delivery, "push_text", lambda token, to, text: pushes.append((token, to, text))
    )
    LineOrLogSender().send(_reminder("r1", "2026-07-02T11:00:00"))
    assert pushes == [("token-1", "sess-1", reminder_text(_reminder("r1", "x")))]


def test_sender_simulates_when_line_not_configured(monkeypatch):
    monkeypatch.setattr(reminder_delivery.config, "load_settings", lambda: _settings(None))
    # Must not raise; delivery is logged as simulated.
    LineOrLogSender().send(_reminder("r1", "2026-07-02T11:00:00"))


def test_sender_simulates_for_email_channel(monkeypatch):
    monkeypatch.setattr(reminder_delivery.config, "load_settings", lambda: _settings("token-1"))
    monkeypatch.setattr(
        reminder_delivery, "push_text", lambda *args: (_ for _ in ()).throw(AssertionError)
    )
    LineOrLogSender().send(_reminder("r1", "2026-07-02T11:00:00", channel="email"))
