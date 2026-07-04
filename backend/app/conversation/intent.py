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
# Statutory requirement for unemployment benefits: separation must be
# involuntary (勞保 failure of employer, layoff, etc.), never a resignation.
_INVOLUNTARY_KEYWORDS = ("被裁", "資遣", "歇業", "倒閉", "關廠", "非自願離職")

_AGE_PATTERNS = [re.compile(r"(\d{1,3})\s*歲"), re.compile(r"今年\s*(\d{1,3})")]

# Income amount: needs an explicit 年/月 prefix — a bare figure (「40萬」) is
# ambiguous and stays unparsed. Certified statuses (低收入戶…) cannot be
# inferred from an amount and keep their own keyword table above.
_INCOME_AMOUNT_PATTERN = re.compile(
    r"(年收入|年薪|年收|月收入|月薪|月領|月收|每月收入|一個月[賺領約]?)"
    r"\s*(?:大約|大概|差不多|約)?\s*"
    r"([0-9零一二兩三四五六七八九十百千萬,.]+)"
)

_ZH_DIGITS = {
    "零": 0,
    "一": 1,
    "二": 2,
    "兩": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}
_ZH_UNITS = {"十": 10, "百": 100, "千": 1000}


def _zh_to_int(section: str) -> int | None:
    """Chinese numeral below 10000 (四十 -> 40, 三千五百 -> 3500, 十五 -> 15)."""
    total = 0
    digit = 0
    seen = False
    for char in section:
        if char in _ZH_DIGITS:
            digit = _ZH_DIGITS[char]
            seen = True
        elif char in _ZH_UNITS:
            total += (digit or 1) * _ZH_UNITS[char]
            digit = 0
            seen = True
        else:
            return None
    return total + digit if seen else None


def _section_value(section: str) -> float | None:
    if re.fullmatch(r"\d+(?:\.\d+)?", section):
        return float(section)
    value = _zh_to_int(section)
    return float(value) if value is not None else None


def parse_income_amount(raw: str) -> int | None:
    """NT$ amount from digits/Chinese numerals: 四十萬, 3.5萬, 45000, 三萬五."""
    text = raw.replace(",", "").rstrip("元")
    if "萬" in text:
        left, _, right = text.partition("萬")
        left_value = _section_value(left)
        if left_value is None:
            return None
        amount = left_value * 10000
        if right:
            right_value = _section_value(right)
            if right_value is None:
                return None
            # Salary shorthand: a single trailing digit means thousands (三萬五).
            amount += right_value * 1000 if len(right) == 1 else right_value
        return int(amount)
    value = _section_value(text)
    return int(value) if value is not None else None


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
        if any(keyword in text for keyword in _INVOLUNTARY_KEYWORDS):
            profile["involuntary_separation"] = True

        for pattern in _AGE_PATTERNS:
            match = pattern.search(text)
            if match:
                profile["age"] = int(match.group(1))
                break

        income_match = _INCOME_AMOUNT_PATTERN.search(text)
        if income_match:
            amount = parse_income_amount(income_match.group(2))
            if amount is not None:
                monthly = amount // 12 if income_match.group(1).startswith("年") else amount
                if 1_000 <= monthly <= 10_000_000:  # sanity range, else ignore
                    profile["monthly_income"] = monthly

        return profile
