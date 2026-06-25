"""Recommendation aggregation: merged document checklist + conflicts (TASK.005)."""

from __future__ import annotations

from app.recommendation import aggregate_documents, build_recommendation
from app.rule_engine import evaluate_all, load_rules

RULES = load_rules()
RULES_BY_ID = {r["id"]: r for r in RULES}

# Profile that makes both housing services and emergency aid possibly qualify.
HOUSING_PROFILE = {
    "residence_city": "Taipei",
    "has_lease": True,
    "income_status": "near_threshold",
    "age": 30,
}


def test_conflicts_detected_between_possible_services():
    evaluations = evaluate_all(RULES, HOUSING_PROFILE)
    rec = build_recommendation(evaluations, RULES_BY_ID)

    possible_ids = {p["service_id"] for p in rec.possible}
    assert {"rent_subsidy_central", "social_housing_taipei"} <= possible_ids
    assert len(rec.conflicts) == 1
    assert rec.conflicts[0]["type"] == "choose_one"
    assert rec.conflicts[0]["service_ids"] == [
        "rent_subsidy_central",
        "social_housing_taipei",
    ]


def test_document_checklist_is_deduplicated_with_attribution():
    evaluations = evaluate_all(RULES, HOUSING_PROFILE)
    rec = build_recommendation(evaluations, RULES_BY_ID)

    names = [item["document"] for item in rec.document_checklist]
    assert len(names) == len(set(names))  # de-duplicated

    id_doc = next(item for item in rec.document_checklist if item["document"] == "身分證明文件")
    # 身分證明文件 is required by several services -> attributed to more than one.
    assert len(id_doc["services"]) >= 2


def test_no_conflict_when_single_possible():
    evaluations = evaluate_all(RULES, {"residence_city": "Taipei", "event_type": "illness"})
    rec = build_recommendation(evaluations, RULES_BY_ID)
    # emergency aid qualifies; housing pair does not -> no choose-one conflict.
    assert rec.conflicts == []


def test_aggregate_documents_empty_when_no_possible():
    assert aggregate_documents([]) == []
