"""Reminder + source-trace endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

FUTURE = "2026-09-01T09:00:00"


def test_create_reminder_requires_consent():
    response = client.post(
        "/reminders",
        json={"session_id": "r1", "reminder_type": "deadline", "scheduled_at": FUTURE},
    )
    assert response.status_code == 403


def test_create_list_and_cancel_reminder():
    create = client.post(
        "/reminders",
        json={
            "session_id": "r2",
            "reminder_type": "deadline",
            "scheduled_at": FUTURE,
            "channel": "line",
            "consent": True,
        },
    )
    assert create.status_code == 201
    reminder_id = create.json()["id"]

    listed = client.get("/reminders/r2").json()["reminders"]
    assert any(r["id"] == reminder_id for r in listed)

    cancelled = client.delete(f"/reminders/{reminder_id}", params={"session_id": "r2"})
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"


def test_cancel_other_session_is_404():
    create = client.post(
        "/reminders",
        json={
            "session_id": "owner-x",
            "reminder_type": "renewal",
            "scheduled_at": FUTURE,
            "consent": True,
        },
    )
    reminder_id = create.json()["id"]
    response = client.delete(f"/reminders/{reminder_id}", params={"session_id": "intruder"})
    assert response.status_code == 404


def test_invalid_reminder_type_is_422():
    response = client.post(
        "/reminders",
        json={
            "session_id": "r3",
            "reminder_type": "bogus",
            "scheduled_at": FUTURE,
            "consent": True,
        },
    )
    assert response.status_code == 422


def test_service_source_trace():
    response = client.get("/services/emergency_aid_taipei/source")
    assert response.status_code == 200
    body = response.json()
    assert body["source"]["url"].startswith("https://")
    assert body["version"]
    assert body["needs_review"] is False


def test_service_source_flags_needs_review():
    body = client.get("/services/unemployment_assistance_central/source").json()
    assert body["needs_review"] is True


def test_unknown_service_source_404():
    assert client.get("/services/does_not_exist/source").status_code == 404


def test_services_listing():
    services = client.get("/services").json()["services"]
    assert len(services) >= 5
    assert all("needs_review" in s for s in services)
