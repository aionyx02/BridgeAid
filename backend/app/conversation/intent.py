"""Intent / field extraction from natural-language messages.

`DeterministicIntentParser` maps keywords to the canonical profile tokens the
rule engine expects (see docs/data.md). It only sets a field when there is a
positive signal — it never guesses False — so unknown fields stay unknown and
the rule engine can ask for them. Booleans are only ever set True here.
"""

from __future__ import annotations

import re
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class IntentParser(Protocol):
    def extract(self, text: str) -> dict[str, Any]:
        """Return the profile fields confidently found in `text` (may be empty)."""
        ...


_CITY_KEYWORDS: list[tuple[tuple[str, ...], str]] = [
    (("臺北", "台北", "北市"), "Taipei"),
    (("高雄", "高市"), "Kaohsiung"),
]

_EVENT_KEYWORDS: list[tuple[tuple[str, ...], str]] = [
    (("失業", "沒工作", "沒有工作", "沒了工作", "被裁", "資遣", "丟了工作"), "unemployment"),
    (("生病", "住院", "傷病", "開刀", "重病", "罹病"), "illness"),
    (("火災", "失火", "火燒"), "fire"),
    (("車禍", "重大事故", "意外事故"), "major_accident"),
    (("過世", "死亡", "往生", "身故", "去世"), "death_in_family"),
]

_INCOME_KEYWORDS: list[tuple[tuple[str, ...], str]] = [
    (("中低收入", "中低收"), "mid_low_income"),
    (("低收入戶", "低收"), "low_income"),
    (("邊緣戶",), "near_threshold"),
    (("收入一般", "一般家庭", "一般戶"), "general"),
]

_LEASE_KEYWORDS = ("租屋", "房租", "租金", "租約", "房東", "承租", "租房")
_CAREGIVER_KEYWORDS = ("照顧", "照護", "顧老", "顧病")
_CARE_NEED_KEYWORDS = ("失能", "臥床", "失智", "重度", "長照需求")
_INSURED_KEYWORDS = ("勞保", "就業保險", "有保勞保")

_AGE_PATTERNS = [re.compile(r"(\d{1,3})\s*歲"), re.compile(r"今年\s*(\d{1,3})")]


def _first_match(text: str, table: list[tuple[tuple[str, ...], str]]) -> str | None:
    for keywords, value in table:
        if any(keyword in text for keyword in keywords):
            return value
    return None


class DeterministicIntentParser:
    """Keyword-based parser. Stateless and dependency-free."""

    def extract(self, text: str) -> dict[str, Any]:
        profile: dict[str, Any] = {}

        city = _first_match(text, _CITY_KEYWORDS)
        if city:
            profile["residence_city"] = city

        event = _first_match(text, _EVENT_KEYWORDS)
        if event:
            profile["event_type"] = event

        income = _first_match(text, _INCOME_KEYWORDS)
        if income:
            profile["income_status"] = income

        if any(keyword in text for keyword in _LEASE_KEYWORDS):
            profile["has_lease"] = True
        if any(keyword in text for keyword in _CAREGIVER_KEYWORDS):
            profile["caregiver"] = True
        if any(keyword in text for keyword in _CARE_NEED_KEYWORDS):
            profile["care_need"] = True
        if any(keyword in text for keyword in _INSURED_KEYWORDS):
            profile["employment_insured"] = True

        for pattern in _AGE_PATTERNS:
            match = pattern.search(text)
            if match:
                profile["age"] = int(match.group(1))
                break

        return profile
