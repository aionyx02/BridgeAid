"""Deterministic intent/field extraction."""

from __future__ import annotations

from app.conversation import DeterministicIntentParser

parser = DeterministicIntentParser()


def test_extracts_city_event_and_lease():
    profile = parser.extract("我最近失業，台北的房租快繳不出來")
    assert profile["residence_city"] == "Taipei"
    assert profile["event_type"] == "unemployment"
    assert profile["has_lease"] is True


def test_extracts_illness_and_age():
    profile = parser.extract("爸爸生病住院，我今年40歲")
    assert profile["event_type"] == "illness"
    assert profile["age"] == 40


def test_extracts_income_and_caregiver():
    profile = parser.extract("我是邊緣戶，要照顧失智的母親")
    assert profile["income_status"] == "near_threshold"
    assert profile["caregiver"] is True
    assert profile["care_need"] is True


def test_unknown_text_returns_empty():
    assert parser.extract("你好") == {}


def test_never_sets_false_booleans():
    # No lease signal -> field stays absent (unknown), not False.
    assert "has_lease" not in parser.extract("我住高雄")


def test_extracts_annual_income_chinese_numerals():
    profile = parser.extract("我年薪四十萬")
    assert profile["monthly_income"] == 400000 // 12


def test_extracts_monthly_income_variants():
    assert parser.extract("月薪3萬5")["monthly_income"] == 35000
    assert parser.extract("月收入大概35,000元")["monthly_income"] == 35000
    assert parser.extract("我一個月賺三萬五")["monthly_income"] == 35000
    assert parser.extract("年收入100萬")["monthly_income"] == 1000000 // 12


def test_bare_amount_without_period_prefix_is_ignored():
    # 「40萬」 alone is ambiguous (annual? monthly? savings?) — never guessed.
    assert "monthly_income" not in parser.extract("大概40萬")


def test_absurd_income_amount_is_ignored():
    assert "monthly_income" not in parser.extract("月薪三")
