"""Evaluator tests: possible / insufficient_data / unlikely, documents, conflicts."""

from __future__ import annotations

import pytest

from app.rule_engine import (
    INSUFFICIENT_DATA,
    POSSIBLE,
    UNLIKELY,
    detect_conflicts,
    evaluate,
    evaluate_all,
    load_rules,
)


@pytest.fixture(scope="module")
def rules_by_id():
    return {rule["id"]: rule for rule in load_rules()}


def test_possible_with_hit_conditions(rules_by_id):
    rule = rules_by_id["emergency_aid_taipei"]
    profile = {"residence_city": "Taipei", "event_type": "illness"}

    result = evaluate(rule, profile)

    assert result.status == POSSIBLE
    hit_fields = {c["field"] for c in result.hit_conditions}
    assert {"residence_city", "event_type"} <= hit_fields
    assert result.missing_fields == []


def test_insufficient_data_collects_missing_fields(rules_by_id):
    rule = rules_by_id["emergency_aid_taipei"]
    profile = {"residence_city": "Taipei"}  # no event_type

    result = evaluate(rule, profile)

    assert result.status == INSUFFICIENT_DATA
    assert "event_type" in result.missing_fields


def test_unlikely_when_hard_condition_fails(rules_by_id):
    rule = rules_by_id["emergency_aid_taipei"]
    profile = {"residence_city": "Kaohsiung", "event_type": "illness"}

    result = evaluate(rule, profile)

    assert result.status == UNLIKELY


def test_numeric_operator_gte(rules_by_id):
    rule = rules_by_id["social_housing_taipei"]
    assert evaluate(rule, {"residence_city": "Taipei", "age": 25}).status == POSSIBLE
    assert evaluate(rule, {"residence_city": "Taipei", "age": 18}).status == POSSIBLE
    assert evaluate(rule, {"residence_city": "Taipei", "age": 17}).status == UNLIKELY


def test_documents_depend_on_event_type(rules_by_id):
    rule = rules_by_id["emergency_aid_taipei"]

    fire = evaluate(rule, {"residence_city": "Taipei", "event_type": "fire"})
    assert "事故證明" in fire.documents
    assert "診斷證明" not in fire.documents
    assert "身分證明文件" in fire.documents  # condition: always

    illness = evaluate(rule, {"residence_city": "Taipei", "event_type": "illness"})
    assert "診斷證明" in illness.documents
    assert "事故證明" not in illness.documents


def test_unemployment_requires_involuntary_separation(rules_by_id):
    rule = rules_by_id["unemployment_assistance_central"]
    profile = {"event_type": "unemployment", "employment_insured": True}
    # 就保法第 11 條：非自願離職是法定要件，未知時只能追問，不可標 possible。
    assert evaluate(rule, profile).status == INSUFFICIENT_DATA
    assert evaluate(rule, {**profile, "involuntary_separation": True}).status == POSSIBLE
    assert evaluate(rule, {**profile, "involuntary_separation": False}).status == UNLIKELY


def test_rent_subsidy_income_amount_or_status(rules_by_id):
    rule = rules_by_id["rent_subsidy_central"]
    base = {"has_lease": True, "age": 40}
    # 115年最低生活費最低縣市（臺灣省 15,515）× 3 = 46,545 為保守門檻。
    low = evaluate(rule, {**base, "monthly_income": 400000 // 12})
    assert low.status == POSSIBLE
    # 高於保守門檻 → 不判 unlikely（各縣市門檻不同），退回追問 income_status。
    high = evaluate(rule, {**base, "monthly_income": 80000})
    assert high.status == INSUFFICIENT_DATA
    assert "income_status" in high.missing_fields
    # 身分別已知時，金額不需要。
    status_only = evaluate(rule, {**base, "income_status": "general"})
    assert status_only.status == POSSIBLE


def test_needs_review_flag(rules_by_id):
    # All bundled services passed policy review; use a copy to test the flag.
    rule = dict(rules_by_id["long_term_care_central"], status="needs_review")
    result = evaluate(rule, {"care_need": True})
    assert result.status == POSSIBLE
    assert result.needs_review is True


def test_evaluate_all_ranks_possible_first(rules_by_id):
    profile = {
        "residence_city": "Taipei",
        "event_type": "unemployment",
        "income_status": "near_threshold",
        "has_lease": True,
        "age": 40,
        "caregiver": True,
    }
    results = evaluate_all(list(rules_by_id.values()), profile)
    statuses = [r.status for r in results]
    assert statuses == sorted(statuses, key={POSSIBLE: 0, INSUFFICIENT_DATA: 1, UNLIKELY: 2}.get)
    assert results[0].status == POSSIBLE


def test_detect_conflicts_choose_one(rules_by_id):
    conflicts = detect_conflicts(["rent_subsidy_central", "social_housing_taipei"], rules_by_id)
    assert len(conflicts) == 1
    assert conflicts[0]["type"] == "choose_one"
    assert conflicts[0]["service_ids"] == ["rent_subsidy_central", "social_housing_taipei"]


def test_no_conflict_when_only_one_selected(rules_by_id):
    assert detect_conflicts(["rent_subsidy_central"], rules_by_id) == []
