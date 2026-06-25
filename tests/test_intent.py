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
