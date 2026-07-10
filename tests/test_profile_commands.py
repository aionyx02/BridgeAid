"""Conversational profile management (我的資料 / 修改 / 清除資料) + 1957 referral."""

from __future__ import annotations

from app.conversation import ConversationManager, InMemorySessionStore
from app.conversation.manager import HOTLINE_1957, KIND_INFO, KIND_QUESTION, KIND_RESULT
from app.rule_engine import load_rules

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


def test_profile_command_when_empty():
    manager, _ = _manager()
    reply = manager.handle_message("p1", "我的資料")
    assert reply.kind == KIND_INFO
    assert "沒有登錄任何資料" in reply.text


def test_profile_command_lists_fields_and_edit_options():
    manager, _ = _manager()
    manager.handle_message("p1", "我住臺北，今年40歲，最近被公司資遣失業")
    reply = manager.handle_message("p1", "我的資料")
    assert reply.kind == KIND_INFO
    assert "居住縣市：臺北市" in reply.text
    assert "年齡：40" in reply.text
    assert "非自願離職：是" in reply.text
    assert "修改年齡" in reply.options
    assert "清除資料" in reply.options


def test_edit_command_reasks_question_and_updates_value():
    manager, store = _manager()
    manager.handle_message("p1", "我住臺北，今年40歲")
    reply = manager.handle_message("p1", "修改年齡")
    assert reply.kind == KIND_QUESTION
    assert "年齡" in reply.text

    manager.handle_message("p1", "35")
    assert store.get("p1", "web").profile["age"] == 35


def test_edit_command_with_unknown_target_lists_editable_fields():
    manager, _ = _manager()
    reply = manager.handle_message("p1", "修改血型")
    assert reply.kind == KIND_INFO
    assert "可修改的項目" in reply.text


def test_profile_command_interrupts_pending_question_safely():
    manager, store = _manager()
    manager.handle_message("p1", "我失業了")  # manager asks a follow-up
    assert store.get("p1", "web").pending_field is not None
    reply = manager.handle_message("p1", "我的資料")
    assert reply.kind == KIND_INFO
    # The command must not be swallowed as an answer to the pending question.
    assert store.get("p1", "web").pending_field is None


def test_clear_command_wipes_profile():
    manager, store = _manager()
    manager.handle_message("p1", "我住臺北，今年40歲")
    reply = manager.handle_message("p1", "清除資料")
    assert reply.kind == KIND_INFO
    assert store.get("p1", "web").profile == {}
    assert store.get("p1", "web").asked_fields == []

    followup = manager.handle_message("p1", "我的資料")
    assert "沒有登錄任何資料" in followup.text


def test_service_list_command():
    manager, _ = _manager()
    reply = manager.handle_message("svc", "服務清單")
    assert reply.kind == KIND_INFO
    assert "中央租金補貼" in reply.text
    assert "臺北市急難救助" in reply.text
    assert "急難救助" in reply.text  # category label
    assert reply.text.count("・") == 6  # all bundled services listed


def _drive_to_result(manager, store, session_id, first_message):
    reply = manager.handle_message(session_id, first_message)
    while reply.kind == KIND_QUESTION:
        pending = store.get(session_id, "web").pending_field
        reply = manager.handle_message(session_id, ANSWERS[pending])
    return reply


def test_unchanged_result_is_not_repeated():
    manager, store = _manager()
    result = _drive_to_result(manager, store, "rep", "我住臺北，40歲，被資遣失業，有勞保，有租約")
    assert result.kind == KIND_RESULT

    again = manager.handle_message("rep", "然後呢")
    assert again.kind == KIND_INFO
    assert "相同" in again.text
    assert "服務清單" in again.options

    # New information changes the outcome -> a fresh result is shown again.
    updated = manager.handle_message("rep", "我還要照顧失智又臥床的爸爸")
    assert updated.kind == KIND_RESULT
    assert "long_term_care_central" in {r["service_id"] for r in updated.results}


def test_near_threshold_result_refers_to_1957():
    manager, store = _manager()
    reply = manager.handle_message("p1", "我住臺北，40歲，被資遣失業，有勞保，有租約，是邊緣戶")
    while reply.kind == KIND_QUESTION:
        reply = manager.handle_message("p1", ANSWERS[store.get("p1", "web").pending_field])
    assert reply.kind == KIND_RESULT
    assert reply.results  # still recommends services
    assert HOTLINE_1957 in reply.text


def test_no_possible_result_refers_to_1957():
    manager, store = _manager()
    # Exhaust the question budget with unhelpful answers -> no possible service.
    reply = manager.handle_message("np1", "你好")
    rounds = 0
    while reply.kind == KIND_QUESTION and rounds < 10:
        rounds += 1
        pending = store.get("np1", "web").pending_field
        reply = manager.handle_message("np1", "其他" if pending == "residence_city" else "你好")
    assert reply.kind == KIND_RESULT
    if not reply.results:
        assert HOTLINE_1957 in reply.text
