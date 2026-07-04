"""Conversation manager: follow-up loop, question cap, session isolation."""

from __future__ import annotations

from app.conversation import (
    MAX_QUESTIONS,
    ConversationManager,
    InMemorySessionStore,
)
from app.conversation.manager import KIND_QUESTION, KIND_RESULT
from app.rule_engine import load_rules

# A valid answer for each field the manager might ask, by option label / free text.
ANSWERS = {
    "residence_city": "臺北市",
    "event_type": "失業",
    "income_status": "邊緣戶",
    "has_lease": "有",
    "age": "40",
    "monthly_income": "35000",
    "employment_insured": "有",
    "involuntary_separation": "是",
    "caregiver": "否",
    "care_need": "否",
}


def _manager():
    store = InMemorySessionStore()
    return ConversationManager(load_rules(), store), store


def test_vague_message_asks_a_question():
    manager, _ = _manager()
    reply = manager.handle_message("s1", "我最近失業，房租快繳不出來")
    assert reply.kind == KIND_QUESTION
    assert reply.text
    assert reply.options  # button-friendly


def test_conversation_converges_to_recommendation_within_cap():
    manager, store = _manager()
    reply = manager.handle_message("s1", "我最近失業，房租快繳不出來，爸爸住院")

    asked = 0
    while reply.kind == KIND_QUESTION:
        asked += 1
        assert asked <= MAX_QUESTIONS
        pending = store.get("s1", "web").pending_field
        reply = manager.handle_message("s1", ANSWERS[pending])

    assert reply.kind == KIND_RESULT
    assert store.get("s1", "web").asked_fields  # at least one question was asked
    assert len(store.get("s1", "web").asked_fields) <= MAX_QUESTIONS
    service_ids = {r["service_id"] for r in reply.results}
    assert "emergency_aid_taipei" in service_ids


def test_result_includes_documents_and_source():
    manager, store = _manager()
    reply = manager.handle_message("s1", "我住臺北，生病住院，是低收入戶")
    # Drive remaining questions to completion.
    while reply.kind == KIND_QUESTION:
        pending = store.get("s1", "web").pending_field
        reply = manager.handle_message("s1", ANSWERS[pending])

    emergency = next(r for r in reply.results if r["service_id"] == "emergency_aid_taipei")
    assert emergency["status"] == "possible"
    assert "診斷證明" in emergency["documents"]
    assert emergency["source"]["url"].startswith("https://")


def test_sessions_are_isolated():
    manager, store = _manager()
    manager.handle_message("a", "我住臺北")
    manager.handle_message("b", "我住高雄")
    assert store.get("a", "web").profile["residence_city"] == "Taipei"
    assert store.get("b", "web").profile["residence_city"] == "Kaohsiung"


def test_salary_only_message_converges_to_rent_subsidy():
    # Regression (2026-07-04): 「我年薪四十萬」 used to burn the question budget
    # on city/event and end at "insufficient, call 1957".
    manager, store = _manager()
    reply = manager.handle_message("s-income", "我年薪四十萬")
    assert store.get("s-income", "web").profile["monthly_income"] == 400000 // 12

    rounds = 0
    while reply.kind == KIND_QUESTION and rounds <= MAX_QUESTIONS:
        rounds += 1
        pending = store.get("s-income", "web").pending_field
        reply = manager.handle_message("s-income", ANSWERS[pending])

    assert reply.kind == KIND_RESULT
    assert "rent_subsidy_central" in {r["service_id"] for r in reply.results}


def test_question_not_repeated():
    manager, store = _manager()
    reply = manager.handle_message("s1", "我失業了")
    asked_seen: list[str] = []
    while reply.kind == KIND_QUESTION:
        pending = store.get("s1", "web").pending_field
        asked_seen.append(pending)
        reply = manager.handle_message("s1", ANSWERS[pending])
    assert len(asked_seen) == len(set(asked_seen))  # no field asked twice
