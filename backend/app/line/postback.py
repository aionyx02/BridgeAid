"""LINE postback parsing + reminder scheduling helpers (TASK.015).

Pure functions so the opt-in reminder flow (ADR-0005) is testable without
FastAPI or the LINE API. Postback data uses querystring form:
``action=remind&service=<id>`` / ``action=remind_ok&service=<id>`` /
``action=remind_no``.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from urllib.parse import parse_qs

LEAD_DAYS = 7
REMIND_HOUR = 9


def parse_postback(data: str) -> dict[str, str]:
    """First value per key from the postback querystring; empty dict if blank."""
    return {key: values[0] for key, values in parse_qs(data or "").items() if values}


def _at_remind_hour(moment: datetime) -> datetime:
    return moment.replace(hour=REMIND_HOUR, minute=0, second=0, microsecond=0)


def earliest_deadline(steps: list[dict[str, Any]]) -> datetime | None:
    """Earliest machine-readable ``deadline_at`` across process steps, if any."""
    deadlines: list[datetime] = []
    for step in steps:
        raw = step.get("deadline_at")
        if not raw:
            continue
        try:
            deadlines.append(datetime.fromisoformat(raw))
        except ValueError:
            continue
    return min(deadlines) if deadlines else None


def reminder_time(steps: list[dict[str, Any]], now: datetime) -> str:
    """When to remind: deadline minus 7 days at 09:00, never earlier than
    tomorrow 09:00; without a deadline, 7 days from now at 09:00."""
    deadline = earliest_deadline(steps)
    base = deadline - timedelta(days=LEAD_DAYS) if deadline else now + timedelta(days=LEAD_DAYS)
    scheduled = _at_remind_hour(base)
    floor = _at_remind_hour(now + timedelta(days=1))
    return max(scheduled, floor).isoformat(timespec="minutes")
