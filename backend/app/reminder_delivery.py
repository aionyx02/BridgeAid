"""Reminder delivery: lightweight in-process scheduler (ADR-0006).

An asyncio loop (started from the FastAPI lifespan) periodically sweeps the
`ReminderStore` for pending reminders whose time has come. Delivery goes
through the `ReminderSender` port: LINE push when the channel is `line` and an
access token is configured, otherwise a log line (simulated delivery). A
failed send stays `pending` and is retried on the next tick; nothing raised
here may ever take the API down.

Message text is a fixed per-type template plus the optional note — never the
citizen's narrative (docs/security.md).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Protocol

from . import config
from .line.client import push_text
from .reminders import STATUS_SENT, Reminder, ReminderStore

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 30.0

_TYPE_LABELS = {
    "document": "記得補齊申請文件",
    "deadline": "申請期限快到了",
    "renewal": "續辦時間到了，記得重新申請",
    "eligibility": "你可能已符合新的服務條件，建議重新試算",
}


def reminder_text(reminder: Reminder) -> str:
    label = _TYPE_LABELS.get(reminder.reminder_type, reminder.reminder_type)
    note = f"（{reminder.note}）" if reminder.note else ""
    return f"BridgeAid 提醒：{label}。{note}實際資格與文件請以承辦單位說明為準。"


class ReminderSender(Protocol):
    def send(self, reminder: Reminder) -> None:
        """Deliver one reminder; raise to signal failure (stays pending)."""
        ...


class LineOrLogSender:
    """Push via LINE when configured; otherwise log a simulated delivery.

    For LINE conversations the session_id is the LINE userId (see
    line/webhook.py), so it doubles as the push target.
    """

    def send(self, reminder: Reminder) -> None:
        settings = config.load_settings()
        if reminder.channel == "line" and settings.line_send_configured:
            push_text(
                settings.line_channel_access_token or "",
                reminder.session_id,
                reminder_text(reminder),
            )
            return
        logger.info(
            "reminder %s delivered (simulated, channel=%s, type=%s)",
            reminder.id,
            reminder.channel,
            reminder.reminder_type,
        )


def _is_due(scheduled_at: str, now: datetime) -> bool:
    due_at = datetime.fromisoformat(scheduled_at)
    if due_at.tzinfo is not None:
        # Compare in local time; `now` is naive local.
        due_at = due_at.astimezone().replace(tzinfo=None)
    return due_at <= now


def deliver_due(store: ReminderStore, sender: ReminderSender, now: datetime | None = None) -> int:
    """Send every pending reminder whose time has come; return the count sent."""
    now = now or datetime.now()
    delivered = 0
    for reminder in store.list_pending():
        if not _is_due(reminder.scheduled_at, now):
            continue
        try:
            sender.send(reminder)
        except Exception:
            logger.exception("reminder %s delivery failed; retrying next tick", reminder.id)
            continue
        reminder.status = STATUS_SENT
        store.save(reminder)
        delivered += 1
    return delivered


async def run_scheduler(
    store: ReminderStore,
    sender: ReminderSender,
    interval_seconds: float = POLL_INTERVAL_SECONDS,
) -> None:
    """Sweep forever. Cancelled by the app's lifespan on shutdown."""
    while True:
        try:
            deliver_due(store, sender)
        except Exception:
            logger.exception("reminder scheduler tick failed")
        await asyncio.sleep(interval_seconds)
