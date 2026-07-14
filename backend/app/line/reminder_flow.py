"""LINE postback flow for opt-in application reminders."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ..reminders import ReminderService
from .flex import remind_consent_message
from .postback import parse_postback, reminder_time


def handle_postback(
    session_id: str,
    data: str,
    rules_by_id: dict[str, dict[str, Any]],
    reminders: ReminderService,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Opt-in reminder flow: ask consent first, store only after remind_ok."""
    fields = parse_postback(data)
    action = fields.get("action")

    if action == "remind_no":
        return [
            {
                "type": "text",
                "text": "好的，先不建立提醒。之後想要提醒時，再點卡片上的「提醒我申請」即可。",
            }
        ]

    rule = rules_by_id.get(fields.get("service", ""))
    if rule is None:
        return []

    if action == "remind":
        return [remind_consent_message(rule["id"], rule["name"])]

    if action == "remind_ok":
        scheduled_at = reminder_time(rule.get("application_process", []), now or datetime.now())
        reminder = reminders.create(
            session_id, "deadline", scheduled_at, "line", consent=True, note=rule["name"]
        )
        when = reminder.scheduled_at.replace("T", " ")
        return [
            {
                "type": "text",
                "text": (
                    f"已建立「{rule['name']}」的申請提醒，"
                    f"預計 {when} 透過 LINE 通知你。提醒可隨時取消。"
                ),
            }
        ]

    return []
