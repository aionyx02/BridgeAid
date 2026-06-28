"""Schema-validation tests for service rules (TASK.002 acceptance: >= 5 rules valid)."""

from __future__ import annotations

import pytest

from app.rule_engine import RuleValidationError, load_rules, validate_rule
from app.rule_engine.loader import SERVICES_DIR


def test_at_least_five_rules_present_and_valid():
    rules = load_rules()
    assert len(rules) >= 5
    ids = [r["id"] for r in rules]
    assert len(ids) == len(set(ids)), "service ids must be unique"


def test_shipped_rules_use_traceable_non_placeholder_sources():
    for rule in load_rules():
        url = rule["source"]["url"]
        assert url.startswith("https://")
        assert "example.gov.tw" not in url


def test_every_shipped_rule_validates():
    for path in SERVICES_DIR.glob("*.json"):
        # load_rules already validates; this asserts each file individually
        from app.rule_engine import load_rule

        load_rule(path)


def test_invalid_rule_is_rejected():
    bad = {
        "id": "Bad Id With Spaces",
        "name": "broken",
        "category": "emergency_aid",
        "jurisdiction": "central",
        "version": "1",
        "eligibility_rules": {"all": [{"field": "x", "operator": "equals", "value": 1}]},
        "source": {
            "title": "t",
            "url": "https://example.gov.tw",
            "last_checked_at": "2026-06-25",
        },
    }
    with pytest.raises(RuleValidationError):
        validate_rule(bad)


def test_unknown_operator_is_rejected():
    bad = {
        "id": "unknown_op",
        "name": "broken",
        "category": "other",
        "jurisdiction": "central",
        "version": "1",
        "eligibility_rules": {"all": [{"field": "x", "operator": "between", "value": 1}]},
        "source": {
            "title": "t",
            "url": "https://example.gov.tw",
            "last_checked_at": "2026-06-25",
        },
    }
    with pytest.raises(RuleValidationError):
        validate_rule(bad)


def test_local_area_requires_value():
    bad = {
        "id": "missing_area_value",
        "name": "broken",
        "category": "housing",
        "jurisdiction": "local",
        "area": {"type": "city"},
        "version": "1",
        "eligibility_rules": {"all": [{"field": "x", "operator": "exists"}]},
        "source": {
            "title": "t",
            "url": "https://example.gov.tw",
            "last_checked_at": "2026-06-25",
        },
    }
    with pytest.raises(RuleValidationError):
        validate_rule(bad)
