"""Follow-up question catalog, keyed by the profile field being asked.

Options use button-friendly labels (low typing burden, docs/ui.md). A value of
``__skip__`` means "free text / none of these" — the field is marked asked so we
never loop, but no value is set.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SKIP = "__skip__"


@dataclass(frozen=True)
class Question:
    field: str
    text: str
    options: list[tuple[str, Any]]  # (label, value); empty options => free text


QUESTIONS: dict[str, Question] = {
    "residence_city": Question(
        "residence_city",
        "請問你目前住在哪個縣市？",
        [("臺北市", "Taipei"), ("高雄市", "Kaohsiung"), ("其他", SKIP)],
    ),
    "event_type": Question(
        "event_type",
        "最近主要發生什麼狀況？",
        [
            ("失業", "unemployment"),
            ("生病/住院", "illness"),
            ("火災", "fire"),
            ("重大事故", "major_accident"),
            ("其他", SKIP),
        ],
    ),
    "income_status": Question(
        "income_status",
        "家庭收入狀況比較接近哪一項？",
        [
            ("低收入戶", "low_income"),
            ("中低收入戶", "mid_low_income"),
            ("邊緣戶", "near_threshold"),
            ("一般", "general"),
        ],
    ),
    "has_lease": Question(
        "has_lease", "你目前有租屋（有租約）嗎？", [("有", True), ("沒有", False)]
    ),
    "age": Question("age", "請問你的年齡？（直接輸入數字即可）", []),
    "employment_insured": Question(
        "employment_insured", "你失業前有投保就業保險（勞保）嗎？", [("有", True), ("沒有", False)]
    ),
    "involuntary_separation": Question(
        "involuntary_separation",
        "離開上一份工作是非自願的嗎？（被資遣、裁員、公司歇業）",
        [("是", True), ("否", False)],
    ),
    "caregiver": Question("caregiver", "你目前是否在照顧家人？", [("是", True), ("否", False)]),
    "care_need": Question(
        "care_need", "需要照顧的家人是否有失能/長照需求？", [("是", True), ("否", False)]
    ),
}
