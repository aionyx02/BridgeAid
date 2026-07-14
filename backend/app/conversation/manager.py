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
MAX_PENDING_RETRIES = 1

KIND_QUESTION = "question"
KIND_RESULT = "result"
KIND_INFO = "info"  # profile summary / confirmation, no eligibility content

STATE_COLLECTING = "collecting"
STATE_AWAITING_ANSWER = "awaiting_answer"
STATE_RESULT_READY = "result_ready"

ANSWER_ACCEPTED = "accepted"
ANSWER_SKIPPED = "skipped"
ANSWER_UNRECOGNIZED = "unrecognized"

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
_SERVICE_COMMANDS = ("服務清單", "服務列表", "有哪些服務", "查看服務")
_EDIT_PREFIX = "修改"

_SKIP_ANSWERS = {"其他", "不知道", "不清楚", "不確定", "跳過", "先跳過"}
_TRUE_ANSWERS = {"有", "是", "對", "對啊", "有的", "yes", "y"}
_FALSE_ANSWERS = {"沒有", "沒", "無", "否", "不是", "沒有喔", "不用", "no", "n"}
_DOCUMENT_FOLLOWUPS = ("文件", "資料", "補件", "準備")
_PROCESS_FOLLOWUPS = ("怎麼申請", "如何申請", "申請流程", "流程", "下一步", "怎麼辦")
_SOURCE_FOLLOWUPS = ("來源", "官方", "查證", "依據")

CATEGORY_LABELS = {
    "emergency_aid": "急難救助",
    "housing": "住宅",
    "long_term_care": "長期照顧",
    "unemployment": "就業/失業",
    "other": "其他",
}

# Edge-case referral: the national welfare consultation hotline is the human
# fallback whenever the rule engine cannot conclude or the case is borderline.
HOTLINE_1957 = "如需進一步協助，可撥打 1957 福利諮詢專線（免付費，每日 8:00–22:00）。"


@dataclass
class Session:
    session_id: str
    channel: str = "web"
    stage: str = STATE_COLLECTING
    profile: dict[str, Any] = field(default_factory=dict)
    asked_fields: list[str] = field(default_factory=list)
    pending_field: str | None = None
    pending_attempts: int = 0
    last_result_text: str | None = None  # dedupe: don't repeat an unchanged result
    last_result_signature: str | None = None
    last_results: list[dict[str, Any]] = field(default_factory=list)
    last_conflicts: list[dict[str, Any]] = field(default_factory=list)
    last_document_checklist: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Reply:
    kind: str  # KIND_QUESTION | KIND_RESULT | KIND_INFO
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


def _normalise_answer(text: str) -> str:
    return "".join(text.strip().split()).replace("台", "臺").lower()


def _apply_answer(session: Session, field_name: str, text: str) -> str:
    answer = text.strip()
    normalised = _normalise_answer(answer)
    if normalised in {_normalise_answer(value) for value in _SKIP_ANSWERS}:
        return ANSWER_SKIPPED

    question = QUESTIONS.get(field_name)
    if question is not None and question.options:
        for label, value in question.options:
            if normalised == _normalise_answer(label):
                if value != SKIP:
                    session.profile[field_name] = value
                    return ANSWER_ACCEPTED
                return ANSWER_SKIPPED
        values = {value for _, value in question.options}
        if values <= {True, False}:
            if normalised in {_normalise_answer(value) for value in _TRUE_ANSWERS}:
                session.profile[field_name] = True
                return ANSWER_ACCEPTED
            if normalised in {_normalise_answer(value) for value in _FALSE_ANSWERS}:
                session.profile[field_name] = False
                return ANSWER_ACCEPTED
    # Free-text / unmatched: let the field-specific or general parser handle it.
    if field_name == "age":
        age_text = answer.removesuffix("歲").removesuffix("歲了").removesuffix("歲左右")
        amount = parse_income_amount(age_text) or (
            int("".join(ch for ch in answer if ch.isdigit()))
            if any(ch.isdigit() for ch in answer)
            else None
        )
        if amount is not None and 1 <= amount <= 120:
            session.profile["age"] = amount
            return ANSWER_ACCEPTED
    elif field_name == "monthly_income":
        # The question already fixes the unit to "per month", so a bare amount
        # (35000 / 3萬5) is unambiguous here, unlike in free conversation.
        amount = parse_income_amount(answer)
        if amount is not None and 1_000 <= amount <= 10_000_000:
            session.profile["monthly_income"] = amount
            return ANSWER_ACCEPTED
    return ANSWER_UNRECOGNIZED


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

        before_profile = dict(session.profile)
        pending_field = session.pending_field
        answer_status = ANSWER_UNRECOGNIZED
        if session.pending_field is not None:
            answer_status = _apply_answer(session, session.pending_field, text)

        session.profile.update(self._parser.extract(text))
        profile_changed = before_profile != session.profile

        if pending_field is not None:
            pending_answered = answer_status in {
                ANSWER_ACCEPTED,
                ANSWER_SKIPPED,
            } or before_profile.get(pending_field) != session.profile.get(pending_field)
            if pending_answered:
                session.pending_field = None
                session.pending_attempts = 0
                session.stage = STATE_COLLECTING
            else:
                session.pending_attempts += 1
                if session.pending_attempts <= MAX_PENDING_RETRIES:
                    reply = self._repeat_pending_reply(session, pending_field, profile_changed)
                    self._store.save(session)
                    return reply
                session.pending_field = None
                session.pending_attempts = 0
                session.stage = STATE_COLLECTING

        if not profile_changed and session.stage == STATE_RESULT_READY:
            followup_reply = self._result_followup_reply(session, text)
            if followup_reply is not None:
                self._store.save(session)
                return followup_reply

        reply = self._next_reply(session)
        if reply.kind == KIND_RESULT:
            signature = _result_signature(reply)
            if signature == session.last_result_signature and not profile_changed:
                # Nothing changed since the last recommendation — repeating the
                # same wall of text reads as the bot being stuck. Point to the
                # ways forward instead.
                reply = Reply(
                    kind=KIND_INFO,
                    text=(
                        "推薦結果和上次相同。想調整可以：直接補充新的情況"
                        "（例如「我住高雄」「月薪3萬5」）、輸入「修改年齡」等指令，"
                        "或「清除資料」重新開始。輸入「服務清單」可看所有服務。"
                    ),
                    options=["我的資料", "服務清單", "需要文件", "申請流程", "清除資料"],
                )
            else:
                self._remember_result(session, reply, signature)
        self._store.save(session)
        return reply

    def _command_reply(self, session: Session, text: str) -> Reply | None:
        """Profile-management commands; None means a normal conversation turn."""
        command = text.strip()
        if command in _CLEAR_COMMANDS:
            session.profile.clear()
            session.asked_fields.clear()
            session.pending_field = None
            session.pending_attempts = 0
            session.stage = STATE_COLLECTING
            session.last_result_text = None
            session.last_result_signature = None
            session.last_results.clear()
            session.last_conflicts.clear()
            session.last_document_checklist.clear()
            return Reply(
                kind=KIND_INFO,
                text="已清除這個對話登錄的所有資料。想重新諮詢時，直接描述你的情況即可。",
            )
        if command in _SERVICE_COMMANDS:
            return self._services_reply()
        if command in _PROFILE_COMMANDS:
            session.pending_field = None
            session.pending_attempts = 0
            return self._profile_reply(session)
        if command.startswith(_EDIT_PREFIX) and len(command) > len(_EDIT_PREFIX):
            session.pending_field = None
            session.pending_attempts = 0
            return self._edit_reply(session, command[len(_EDIT_PREFIX) :].strip())
        return None

    def _services_reply(self) -> Reply:
        """Catalog of every bundled service, grouped as a readable list."""
        lines = []
        for rule in self._rules:
            category = CATEGORY_LABELS.get(rule.get("category", "other"), "其他")
            suffix = "（資料待人工確認）" if rule.get("status") == "needs_review" else ""
            lines.append(f"・{rule['name']}｜{category}{suffix}")
        return Reply(
            kind=KIND_INFO,
            text=(
                "目前可協助評估的服務：\n"
                + "\n".join(lines)
                + "\n直接描述你的情況（例如「我被資遣了，房租繳不出來」），"
                "我會判斷你可能符合哪些。"
            ),
            options=["我的資料", "清除資料"],
        )

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
                session.pending_attempts = 0
                session.stage = STATE_AWAITING_ANSWER
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
            session.pending_attempts = 0
            session.stage = STATE_AWAITING_ANSWER
            question = QUESTIONS[next_field]
            return Reply(
                kind=KIND_QUESTION,
                text=question.text,
                options=[label for label, _ in question.options],
            )

        session.stage = STATE_RESULT_READY
        return self._result_reply(evaluations, session.profile)

    def _repeat_pending_reply(
        self, session: Session, field_name: str, profile_changed: bool
    ) -> Reply:
        question = QUESTIONS[field_name]
        session.pending_field = field_name
        session.stage = STATE_AWAITING_ANSWER
        prefix = (
            "我先記下你補充的資訊，不過這一題還需要確認："
            if profile_changed
            else "我還無法判斷這一題，請再回答一次："
        )
        return Reply(
            kind=KIND_QUESTION,
            text=prefix + question.text,
            options=[label for label, _ in question.options],
        )

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

    def _remember_result(self, session: Session, reply: Reply, signature: str) -> None:
        session.stage = STATE_RESULT_READY
        session.last_result_text = reply.text
        session.last_result_signature = signature
        session.last_results = [dict(result) for result in reply.results]
        session.last_conflicts = [dict(conflict) for conflict in reply.conflicts]
        session.last_document_checklist = [dict(item) for item in reply.document_checklist]

    def _result_followup_reply(self, session: Session, text: str) -> Reply | None:
        command = text.strip()
        if any(marker in command for marker in _DOCUMENT_FOLLOWUPS):
            return self._document_followup_reply(session)
        if any(marker in command for marker in _PROCESS_FOLLOWUPS):
            return self._process_followup_reply(session)
        if any(marker in command for marker in _SOURCE_FOLLOWUPS):
            return self._source_followup_reply(session)
        return None

    def _document_followup_reply(self, session: Session) -> Reply:
        if not session.last_document_checklist:
            return Reply(
                kind=KIND_INFO,
                text="目前沒有可彙整的文件清單；你可以補充情況，或洽詢承辦單位確認。",
                options=["我的資料", "服務清單", "申請流程"],
            )
        lines = ["目前建議先準備："]
        for item in session.last_document_checklist:
            service_names = "、".join(self._service_name(sid) for sid in item["services"])
            lines.append(f"・{item['document']}（{service_names}）")
        return Reply(
            kind=KIND_INFO,
            text="\n".join(lines),
            options=["申請流程", "我的資料", "清除資料"],
            document_checklist=session.last_document_checklist,
        )

    def _process_followup_reply(self, session: Session) -> Reply:
        lines = ["申請流程可以先照這個順序確認："]
        found = False
        for service in session.last_results:
            steps = service.get("application_process", [])
            if not steps:
                continue
            found = True
            lines.append(f"\n{service['service_name']}")
            for index, step in enumerate(steps, start=1):
                line = f"{index}. {step['name']}：{step['description']}"
                if step.get("deadline"):
                    line += f"（期限：{step['deadline']}）"
                if step.get("url"):
                    line += f" {step['url']}"
                lines.append(line)
        if not found:
            return Reply(
                kind=KIND_INFO,
                text="目前推薦結果沒有可機讀的申請流程；建議查看官方來源或洽承辦單位確認。",
                options=["來源", "我的資料", "服務清單"],
            )
        return Reply(
            kind=KIND_INFO,
            text="\n".join(lines),
            options=["需要文件", "來源", "我的資料"],
            results=session.last_results,
        )

    def _source_followup_reply(self, session: Session) -> Reply:
        if not session.last_results:
            return Reply(
                kind=KIND_INFO,
                text="目前沒有推薦結果可查來源；你可以先描述情況，我會再列出可追溯的服務來源。",
                options=["服務清單", "我的資料"],
            )
        lines = ["目前推薦結果的來源："]
        for service in session.last_results:
            source = service.get("source") or {}
            checked = source.get("last_checked_at", "未提供")
            url = source.get("url", "未提供")
            lines.append(f"・{service['service_name']}：{url}（檢查日期：{checked}）")
        return Reply(
            kind=KIND_INFO,
            text="\n".join(lines),
            options=["申請流程", "需要文件", "我的資料"],
            results=session.last_results,
        )

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


def _result_signature(reply: Reply) -> str:
    service_ids = ",".join(result["service_id"] for result in reply.results)
    conflicts = ",".join(
        "+".join(conflict["service_ids"]) + ":" + conflict["type"] for conflict in reply.conflicts
    )
    return f"services={service_ids}|conflicts={conflicts}|empty={not reply.results}"
