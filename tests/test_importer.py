"""Importer transform and repository-port behavior (no live database)."""

from __future__ import annotations

from app.importer import ImportSummary, ServiceRows, import_rules, rule_to_rows
from app.rule_engine import load_rules


def _emergency_rule():
    return next(r for r in load_rules() if r["id"] == "emergency_aid_taipei")


def test_rule_to_rows_maps_core_fields():
    rows = rule_to_rows(_emergency_rule())
    assert rows.service["id"] == "emergency_aid_taipei"
    assert rows.service["category"] == "emergency_aid"
    assert rows.service["area_type"] == "city"
    assert rows.service["area_value"] == "Taipei"
    assert rows.version["version"] == rows.eligibility["version"]
    assert rows.eligibility["rule_jsonb"]  # carries the eligibility tree
    assert any(doc["document_name"] == "身分證明文件" for doc in rows.documents)
    assert rows.source["url"].startswith("https://")


def test_rule_to_rows_maps_conflicts():
    rule = next(r for r in load_rules() if r["id"] == "rent_subsidy_central")
    rows = rule_to_rows(rule)
    assert rows.conflicts[0]["conflict_service_id"] == "social_housing_taipei"
    assert rows.conflicts[0]["conflict_type"] == "choose_one"


class FakeRepository:
    def __init__(self):
        self.saved: list[ServiceRows] = []

    def save(self, rows: ServiceRows) -> None:
        self.saved.append(rows)


def test_import_rules_persists_all_and_counts():
    rules = load_rules()
    repo = FakeRepository()

    summary = import_rules(rules, repo)

    assert isinstance(summary, ImportSummary)
    assert summary.services == len(rules)
    assert len(repo.saved) == len(rules)
    assert summary.documents >= len(rules)  # every rule has >= 1 document
    assert summary.conflicts >= 2  # the housing pair declares conflicts both ways
