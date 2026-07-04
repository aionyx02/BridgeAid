"""/chat endpoint: multi-turn conversation over HTTP."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.conversation import MAX_QUESTIONS
from app.main import app

client = TestClient(app)


def _post(session_id: str, message: str) -> dict:
    response = client.post("/chat", json={"session_id": session_id, "message": message})
    assert response.status_code == 200
    return response.json()


def test_first_turn_asks_a_question():
    reply = _post("chat-q", "我最近失業，房租快繳不出來")
    assert reply["kind"] == "question"
    assert reply["text"]
    assert reply["options"]


def test_conversation_converges_to_result_over_http():
    session = "chat-converge"
    reply = _post(session, "我最近失業，房租快繳不出來，爸爸住院")

    turns = 0
    while reply["kind"] == "question":
        turns += 1
        assert turns <= MAX_QUESTIONS
        answer = reply["options"][0] if reply["options"] else "40"
        reply = _post(session, answer)

    assert reply["kind"] == "result"
    assert reply["results"]
    assert any(r["status"] == "possible" for r in reply["results"])
    assert reply["document_checklist"]  # merged checklist included (TASK.005)
