"""Postback parsing, reminder scheduling, and the opt-in webhook flow."""

from __future__ import annotations

import json
from datetime import datetime

from fastapi.testclient import TestClient

import app.main as main
from app.config import Settings
from app.line.postback import parse_postback, reminder_time
from app.line.webhook import expected_signature
from app.main import app

client = TestClient(app)

NOW = datetime(2026, 7, 4, 15, 30)


def test_parse_postback():
    assert parse_postback("action=remind&service=x") == {"action": "remind", "service": "x"}
    assert parse_postback("") == {}


def test_reminder_time_seven_days_before_deadline():
    steps = [{"name": "s", "description": "d", "deadline_at": "2026-12-31"}]
    assert reminder_time(steps, NOW) == "2026-12-24T09:00"


def test_reminder_time_without_deadline_is_week_ahead():
    assert reminder_time([], NOW) == "2026-07-11T09:00"


def test_reminder_time_never_in_the_past():
    steps = [{"name": "s", "description": "d", "deadline_at": "2026-07-05"}]
    assert reminder_time(steps, NOW) == "2026-07-05T09:00"  # tomorrow, not June


def test_reminder_time_ignores_malformed_deadline():
    steps = [{"name": "s", "description": "d", "deadline_at": "下半年"}]
    assert reminder_time(steps, NOW) == "2026-07-11T09:00"


class RecordingReplyClient:
    def __init__(self) -> None:
        self.sent: list[list[dict]] = []

    def reply(self, access_token, reply_token, reply) -> None:  # pragma: no cover
        raise AssertionError("postback flow must use reply_messages")

    def reply_messages(self, access_token, reply_token, messages) -> None:
        self.sent.append(messages)


SECRET = "postback_test_secret"
SETTINGS = Settings(
    line_channel_id="cid",
    line_channel_secret=SECRET,
    line_channel_access_token="token",
    database_url=None,
)


def _post_event(event: dict) -> dict:
    body = json.dumps({"events": [event]}).encode()
    response = client.post(
        "/line/webhook",
        content=body,
        headers={"X-Line-Signature": expected_signature(SECRET, body)},
    )
    assert response.status_code == 200
    return response.json()


def _postback_event(data: str, user_id: str) -> dict:
    return {
        "type": "postback",
        "replyToken": "rt-1",
        "source": {"type": "user", "userId": user_id},
        "postback": {"data": data},
    }


def test_webhook_postback_remind_then_ok_creates_reminder(monkeypatch):
    recorder = RecordingReplyClient()
    monkeypatch.setattr(main, "reply_client", recorder)
    monkeypatch.setattr(main.config, "load_settings", lambda: SETTINGS)

    _post_event(_postback_event("action=remind&service=rent_subsidy_central", "U-pb-1"))
    consent = recorder.sent[0][0]
    assert "同意" in consent["quickReply"]["items"][0]["action"]["label"]

    _post_event(_postback_event("action=remind_ok&service=rent_subsidy_central", "U-pb-1"))
    assert "已建立" in recorder.sent[1][0]["text"]

    reminders = client.get("/reminders/U-pb-1").json()["reminders"]
    assert len(reminders) == 1
    assert reminders[0]["reminder_type"] == "deadline"
    assert reminders[0]["status"] == "pending"


def test_webhook_postback_decline_creates_nothing(monkeypatch):
    recorder = RecordingReplyClient()
    monkeypatch.setattr(main, "reply_client", recorder)
    monkeypatch.setattr(main.config, "load_settings", lambda: SETTINGS)

    _post_event(_postback_event("action=remind_no", "U-pb-2"))
    assert "先不建立" in recorder.sent[0][0]["text"]
    assert client.get("/reminders/U-pb-2").json()["reminders"] == []


def test_webhook_postback_unknown_service_is_ignored(monkeypatch):
    recorder = RecordingReplyClient()
    monkeypatch.setattr(main, "reply_client", recorder)
    monkeypatch.setattr(main.config, "load_settings", lambda: SETTINGS)

    _post_event(_postback_event("action=remind&service=nope", "U-pb-3"))
    assert recorder.sent == []
