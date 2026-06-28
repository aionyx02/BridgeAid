"""Week 7 demo scenarios: intent extraction + explainable recommendations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.conversation.intent import DeterministicIntentParser
from app.recommendation import build_recommendation
from app.rule_engine import evaluate_all, load_rules

SCENARIO_PATH = Path(__file__).parent / "fixtures" / "demo_scenarios.json"
SCENARIOS: list[dict[str, Any]] = json.loads(SCENARIO_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def rules() -> list[dict[str, Any]]:
    return load_rules()


@pytest.fixture(scope="module")
def rules_by_id(rules: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {rule["id"]: rule for rule in rules}


def _id(scenario: dict[str, Any]) -> str:
    return str(scenario["id"])


def test_demo_fixture_has_week_7_scenario_count() -> None:
    ids = [_id(scenario) for scenario in SCENARIOS]
    assert 10 <= len(SCENARIOS) <= 20
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("scenario", SCENARIOS, ids=_id)
def test_demo_scenario_parser_extracts_expected_profile(scenario: dict[str, Any]) -> None:
    profile = DeterministicIntentParser().extract(scenario["message"])

    for field, expected in scenario["expected_profile"].items():
        assert profile.get(field) == expected


@pytest.mark.parametrize("scenario", SCENARIOS, ids=_id)
def test_demo_scenario_recommends_expected_services(
    scenario: dict[str, Any],
    rules: list[dict[str, Any]],
    rules_by_id: dict[str, dict[str, Any]],
) -> None:
    profile = DeterministicIntentParser().extract(scenario["message"])
    evaluations = evaluate_all(rules, profile)
    recommendation = build_recommendation(evaluations, rules_by_id)

    possible_ids = {service["service_id"] for service in recommendation.possible}
    assert set(scenario["expected_possible"]) <= possible_ids
    assert possible_ids <= set(rules_by_id)

    for service in recommendation.possible:
        assert service["source"]["url"].startswith("https://")
        assert "example.gov.tw" not in service["source"]["url"]

    needs_review_ids = {
        service["service_id"] for service in recommendation.possible if service["needs_review"]
    }
    assert set(scenario["expected_needs_review"]) <= needs_review_ids

    conflict_pairs = {tuple(conflict["service_ids"]) for conflict in recommendation.conflicts}
    for pair in scenario["expected_conflicts"]:
        assert tuple(sorted(pair)) in conflict_pairs
