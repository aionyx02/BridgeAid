"""FastAPI endpoint tests (degraded mode: no DB, controlled secrets)."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app import config, main
from app.line.webhook import expected_signature
from app.main import app

client = TestClient(app)

SECRET = "webhook_secret"


def test_healthz_reports_rules_and_config_flags():
    body = client.get("/healthz").json()
    assert body["status"] == "ok"
    assert body["rules_loaded"] >= 5
    assert isinstance(body["line_configured"], bool)
    assert isinstance(body["db_configured"], bool)


def test_recommend_returns_possible_for_matching_profile():
    response = client.post(
        "/recommend",
        json={"profile": {"residence_city": "Taipei", "event_type": "illness"}},
    )
    assert response.status_code == 200
    results = response.json()["results"]
    emergency = next(r for r in results if r["service_id"] == "emergency_aid_taipei")
    assert emergency["status"] == "possible"
    assert "診斷證明" in emergency["documents"]


def test_recommend_insufficient_data():
    response = client.post(
        "/recommend", json={"profile": {"residence_city": "Taipei"}}
    )
    emergency = next(
        r for r in response.json()["results"] if r["service_id"] == "emergency_aid_taipei"
    )
    assert emergency["status"] == "insufficient_data"
    assert "event_type" in emergency["missing_fields"]


def _settings(secret=None):
    return config.Settings(
        line_channel_id="channel-id" if secret else None,
        line_channel_secret=secret,
        line_channel_access_token="token" if secret else None,
        database_url=None,
    )


def test_recommend_includes_conflicts_and_checklist():
    response = client.post(
        "/recommend",
        json={
            "profile": {
                "residence_city": "Taipei",
                "has_lease": True,
                "income_status": "near_threshold",
                "age": 30,
            }
        },
    )
    body = response.json()
    assert any(c["type"] == "choose_one" for c in body["conflicts"])
    assert body["document_checklist"]


def test_webhook_503_when_not_configured(monkeypatch):
    monkeypatch.setattr(config, "load_settings", lambda: _settings())
    response = client.post("/line/webhook", content=b"{}")
    assert response.status_code == 503


def test_webhook_accepts_valid_signature(monkeypatch):
    monkeypatch.setattr(config, "load_settings", lambda: _settings(SECRET))
    body = b'{"events":[]}'
    headers = {"X-Line-Signature": expected_signature(SECRET, body)}
    response = client.post("/line/webhook", content=body, headers=headers)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_webhook_rejects_invalid_signature(monkeypatch):
    monkeypatch.setattr(config, "load_settings", lambda: _settings(SECRET))
    response = client.post(
        "/line/webhook", content=b'{"events":[]}', headers={"X-Line-Signature": "bad"}
    )
    assert response.status_code == 401


def test_webhook_runs_conversation_and_replies(monkeypatch):
    monkeypatch.setattr(config, "load_settings", lambda: _settings(SECRET))

    captured = []

    class FakeReplyClient:
        def reply(self, access_token, reply_token, reply):
            captured.append((access_token, reply_token, reply))

    monkeypatch.setattr(main, "reply_client", FakeReplyClient())

    body = json.dumps(
        {
            "events": [
                {
                    "type": "message",
                    "message": {"type": "text", "text": "我最近失業，房租快繳不出來"},
                    "replyToken": "rt1",
                    "source": {"userId": "u-webhook-1"},
                }
            ]
        }
    ).encode("utf-8")
    headers = {"X-Line-Signature": expected_signature(SECRET, body)}

    response = client.post("/line/webhook", content=body, headers=headers)
    assert response.status_code == 200
    assert len(captured) == 1
    access_token, reply_token, reply = captured[0]
    assert access_token == "token"
    assert reply_token == "rt1"
    assert reply.text


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__]))
