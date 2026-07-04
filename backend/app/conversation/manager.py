"""Conversation manager: session state + rule-engine-driven follow-up.

Each turn: apply any pending answer, extract fields from the message, evaluate
all rules, then either ask the single most useful missing field (capped at
MAX_QUESTIONS) or return a recommendation summary. Eligibility is always the
rule engine's call; this layer only gathers fields and presents results.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Protocol

from ..recommendation import build_recommendation
from ..rule_engine import evaluate_all
from .intent import DeterministicIntentParser, IntentParser, parse_income_amount
from .questions import QUESTIONS, SKIP

MAX_QUESTIONS = 5

KIND_QUESTION = "question"
KIND_RESULT = "result"
KIND_INFO = "info"  # profile summary / confirmation, no eligibility content

# Conversational profile management (TASK.016): view, edit, clear.
FIELD_LABELS: dict[str, str] = {
    "residence_city": "居住縣市",
    "event_type": "遭遇狀況",
    "income_status": "家庭收入狀況",
    "has_lease": "是否有租約",
    "age": "年齡",
    "monthly_income": "每月收入",
    "employment_insured": "就業保險",
    "involuntary_separation": "非自願離職",
    "caregiver": "照顧家人",
    "care_need": "家人長照需求",
}
_PROFILE_COMMANDS = ("我的資料", "查看資料", "查看我的資料")
_CLEAR_COMMANDS = ("清除資料", "清除我的資料", "刪除資料")
_EDIT_PREFIX = "修改"

# Edge-case referral: the national welfare consultation hotline is the human
# fallback whenever the rule engine cannot conclude or the case is borderline.
HOTLINE_1957 = "如需進一步協助，可撥打 1957 福利諮詢專線（免付費，每日 8:00–22:00）。"


@dataclass
class Session:
    session_id: str
    channel: str = "web"
    profile: dict[str, Any] = field(default_factory=dict)
    asked_fields: list[str] = field(default_factory=list)
    pending_field: str | None = None


@dataclass
class Reply:
    kind: str  # KIND_QUESTION | KIND_RESULT
    text: str
    options: list[str] = field(default_factory=list)
    results: list[dict[str, Any]] = field(default_factory=list)
    conflicts: list[dict[str, Any]] = field(default_factory=list)
    document_checklist: list[dict[str, Any]] = field(default_factory=list)


class SessionStore(Protocol):
    def get(self, session_id: str, channel: str) -> Session: ...
    def save(self, session: Session) -> None: ...


class InMemorySessionStore:
    """Process-local session store. Swap for a DB-backed store later."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def get(self, session_id: str, channel: str) -> Session:
        session = self._sessions.get(session_id)
        if session is None:
            session = Session(session_id=session_id, channel=channel)
        return session

    def save(self, session: Session) -> None:
        self._sessions[session.session_id] = session


def _apply_answer(session: Session, field_name: str, text: str) -> None:
    answer = text.strip()
    question = QUESTIONS.get(field_name)
    if question is not None and question.options:
        for label, value in question.options:
            if answer == label:
                if value != SKIP:
                    session.profile[field_name] = value
                return
    # Free-text / unmatched: let the field-specific or general parser handle it.
    if field_name == "age":
        digits = "".join(ch for ch in answer if ch.isdigit())
        if digits:
            session.profile["age"] = int(digits)
    elif field_name == "monthly_income":
        # The question already fixes the unit to "per month", so a bare amount
        # (35000 / 3萬5) is unambiguous here, unlike in free conversation.
        amount = parse_income_amount(answer)
        if amount is not None and 1_000 <= amount <= 10_000_000:
            session.profile["monthly_income"] = amount


def _value_label(field_name: str, value: Any) -> str:
    """Human-readable value: prefer the question option label over the token."""
    question = QUESTIONS.get(field_name)
    if question is not None:
        for label, option_value in question.options:
            if option_value == value:
                return label
    if isinstance(value, bool):
        return "是" if value else "否"
    return str(value)


class ConversationManager:
    def __init__(
        self,
        rules: list[dict[str, Any]],
        store: SessionStore,
        parser: IntentParser | None = None,
    ) -> None:
        self._rules = rules
        self._rules_by_id = {rule["id"]: rule for rule in rules}
        self._store = store
        self._parser = parser or DeterministicIntentParser()

    def handle_message(self, session_id: str, text: str, channel: str = "web") -> Reply:
        session = self._store.get(session_id, channel)
        session.channel = channel

        command_reply = self._command_reply(session, text)
        if command_reply is not None:
            self._store.save(session)
            return command_reply

        if session.pending_field is not None:
            _apply_answer(session, session.pending_field, text)
            session.pending_field = None

        session.profile.update(self._parser.extract(text))

        reply = self._next_reply(session)
        self._store.save(session)
        return reply

    def _command_reply(self, session: Session, text: str) -> Reply | None:
        """Profile-management commands; None means a normal conversation turn."""
        command = text.strip()
        if command in _CLEAR_COMMANDS:
            session.profile.clear()
            session.asked_fields.clear()
            session.pending_field = None
            return Reply(
                kind=KIND_INFO,
                text="已清除這個對話登錄的所有資料。想重新諮詢時，直接描述你的情況即可。",
            )
        if command in _PROFILE_COMMANDS:
            session.pending_field = None
            return self._profile_reply(session)
        if command.startswith(_EDIT_PREFIX) and len(command) > len(_EDIT_PREFIX):
            session.pending_field = None
            return self._edit_reply(session, command[len(_EDIT_PREFIX) :].strip())
        return None

    def _profile_reply(self, session: Session) -> Reply:
        if not session.profile:
            return Reply(
                kind=KIND_INFO,
                text="目前沒有登錄任何資料。直接描述你的情況，需要時我會再逐項詢問。",
            )
        lines = [
            f"・{FIELD_LABELS.get(name, name)}：{_value_label(name, value)}"
            for name, value in session.profile.items()
        ]
        options = [
            f"{_EDIT_PREFIX}{FIELD_LABELS[name]}"
            for name in session.profile
            if name in FIELD_LABELS
        ]
        options.append("清除資料")
        return Reply(
            kind=KIND_INFO,
            text=(
                "你目前登錄的資料：\n"
                + "\n".join(lines)
                + "\n資料只用於本次諮詢比對，可以隨時修改或清除。"
            ),
            options=options,
        )

    def _edit_reply(self, session: Session, target: str) -> Reply:
        for field_name, label in FIELD_LABELS.items():
            if target in (label, field_name):
                question = QUESTIONS[field_name]
                session.pending_field = field_name
                if field_name not in session.asked_fields:
                    session.asked_fields.append(field_name)
                return Reply(
                    kind=KIND_QUESTION,
                    text=question.text,
                    options=[label for label, _ in question.options],
                )
        editable = "、".join(FIELD_LABELS.values())
        return Reply(
            kind=KIND_INFO,
            text=f"可修改的項目：{editable}。請輸入「修改＋項目名稱」，例如「修改年齡」。",
        )

    def _next_reply(self, session: Session) -> Reply:
        evaluations = evaluate_all(self._rules, session.profile)

        next_field = self._pick_next_field(evaluations, session.asked_fields)
        if next_field is not None and len(session.asked_fields) < MAX_QUESTIONS:
            session.asked_fields.append(next_field)
            session.pending_field = next_field
            question = QUESTIONS[next_field]
            return Reply(
                kind=KIND_QUESTION,
                text=question.text,
                options=[label for label, _ in question.options],
            )

        return self._result_reply(evaluations, session.profile)

    @staticmethod
    def _pick_next_field(evaluations: list[Any], asked_fields: list[str]) -> str | None:
        """Ask for the service closest to a decision, not the globally common field.

        The question budget is small, so completing one nearly-decidable service
        beats spreading questions across all of them (e.g. a nationwide subsidy
        must not wait behind city/event questions it does not need). Services the
        user's own words already engaged (hit_conditions non-empty) come first —
        volunteering a salary should steer questions toward the subsidy that
        salary matched, not toward an unrelated service that happens to be one
        field short. Among the chosen service's blockers, prefer the one most
        shared with other services; ties break by rule order -> deterministic.
        """
        counter: Counter[str] = Counter()
        best_key: tuple[int, int] | None = None
        best_askable: list[str] = []
        for evaluation in evaluations:
            if evaluation.status != "insufficient_data":
                continue
            askable = [
                missing
                for missing in evaluation.missing_fields
                if missing in QUESTIONS and missing not in asked_fields
            ]
            if not askable:
                continue
            counter.update(askable)
            key = (0 if evaluation.hit_conditions else 1, len(askable))
            if best_key is None or key < best_key:
                best_key = key
                best_askable = askable
        if best_key is None:
            return None
        return max(best_askable, key=lambda field_name: counter[field_name])

    def _service_name(self, service_id: str) -> str:
        rule = self._rules_by_id.get(service_id)
        return rule["name"] if rule else service_id

    def _result_reply(self, evaluations: list[Any], profile: dict[str, Any]) -> Reply:
        recommendation = build_recommendation(evaluations, self._rules_by_id)
        if not recommendation.possible:
            return Reply(
                kind=KIND_RESULT,
                text=(
                    "目前提供的資訊還不足以判斷可能符合的服務，"
                    "建議洽詢居住地公所或社會局確認。" + HOTLINE_1957
                ),
            )
        names = "、".join(service["service_name"] for service in recommendation.possible)
        text = (
            f"根據你提供的資訊，你「可能符合」以下服務：{names}。實際仍需由承辦單位依正式資料確認。"
        )
        if recommendation.conflicts:
            pairs = "；".join(
                "、".join(self._service_name(sid) for sid in c["service_ids"])
                for c in recommendation.conflicts
            )
            text += f"（注意：部分服務可能需擇一：{pairs}）"
        if profile.get("income_status") == "near_threshold":
            # Borderline household: thresholds are close calls — route to a human.
            text += HOTLINE_1957
        return Reply(
            kind=KIND_RESULT,
            text=text,
            results=recommendation.possible,
            conflicts=recommendation.conflicts,
            document_checklist=recommendation.document_checklist,
        )
