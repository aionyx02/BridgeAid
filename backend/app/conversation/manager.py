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
from .intent import DeterministicIntentParser, IntentParser
from .questions import QUESTIONS, SKIP

MAX_QUESTIONS = 3

KIND_QUESTION = "question"
KIND_RESULT = "result"


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

        if session.pending_field is not None:
            _apply_answer(session, session.pending_field, text)
            session.pending_field = None

        session.profile.update(self._parser.extract(text))

        reply = self._next_reply(session)
        self._store.save(session)
        return reply

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

        return self._result_reply(evaluations)

    @staticmethod
    def _pick_next_field(evaluations: list[Any], asked_fields: list[str]) -> str | None:
        """Most common blocking field across services that could still qualify."""
        counter: Counter[str] = Counter()
        for evaluation in evaluations:
            if evaluation.status != "insufficient_data":
                continue
            for missing in evaluation.missing_fields:
                if missing in QUESTIONS and missing not in asked_fields:
                    counter[missing] += 1
        if not counter:
            return None
        # most_common breaks ties by insertion order -> deterministic
        return counter.most_common(1)[0][0]

    def _result_reply(self, evaluations: list[Any]) -> Reply:
        recommendation = build_recommendation(evaluations, self._rules_by_id)
        if not recommendation.possible:
            return Reply(
                kind=KIND_RESULT,
                text="目前提供的資訊還不足以判斷可能符合的服務，建議洽詢居住地公所或社會局確認。",
            )
        names = "、".join(service["service_name"] for service in recommendation.possible)
        text = (
            f"根據你提供的資訊，你「可能符合」以下服務：{names}。"
            "實際仍需由承辦單位依正式資料確認。"
        )
        if recommendation.conflicts:
            pairs = "；".join("、".join(c["service_ids"]) for c in recommendation.conflicts)
            text += f"（注意：部分服務可能需擇一：{pairs}）"
        return Reply(
            kind=KIND_RESULT,
            text=text,
            results=recommendation.possible,
            conflicts=recommendation.conflicts,
            document_checklist=recommendation.document_checklist,
        )
