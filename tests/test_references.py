"""Reference datasets: schema, expiry guard, ref resolution, no-hardcode guard."""

from __future__ import annotations

from datetime import date

import pytest

from app.rule_engine import (
    INSUFFICIENT_DATA,
    POSSIBLE,
    ReferenceValidationError,
    evaluate,
    load_references,
    load_rules,
    validate_reference,
)

# Fields whose thresholds come from annually-updated official figures.
# Rules must reference a dataset (`ref`) for these — hardcoding the derived
# number is exactly the bug this guard exists to prevent (ADR-0008).
REFERENCE_DERIVED_FIELDS = {"monthly_income"}


@pytest.fixture(scope="module")
def rent_rule():
    return next(rule for rule in load_rules() if rule["id"] == "rent_subsidy_central")


def _conditions(node):
    if "all" in node or "any" in node:
        for child in node.get("all") or node.get("any"):
            yield from _conditions(child)
    else:
        yield node


def test_minimum_living_cost_dataset_loaded():
    dataset = load_references()["minimum_living_cost"]
    assert dataset["values"]["Taipei"] == 20744
    assert dataset["values"]["Kaohsiung"] == 16970
    assert dataset["default"] == 15515
    assert all(source["url"].startswith("https://") for source in dataset["sources"])


def test_reference_schema_rejects_missing_sources():
    with pytest.raises(ReferenceValidationError):
        validate_reference(
            {
                "id": "x",
                "unit": "TWD",
                "period": {"valid_from": "2026-01-01", "valid_to": "2026-12-31"},
                "values": {},
                "default": 1,
            }
        )


def test_reference_datasets_not_expired():
    # Intentional annual tripwire: when a dataset's validity period lapses,
    # this fails until the new official figures are audited in.
    today = date.today().isoformat()
    for dataset in load_references().values():
        period = dataset["period"]
        assert period["valid_from"] <= today <= period["valid_to"], (
            f"reference dataset '{dataset['id']}' is outside its validity period "
            f"({period['valid_from']}..{period['valid_to']}) — re-audit the official figures"
        )


def test_no_hardcoded_reference_derived_thresholds():
    for rule in load_rules():
        for condition in _conditions(rule["eligibility_rules"]):
            if condition["field"] in REFERENCE_DERIVED_FIELDS and condition["operator"] != "exists":
                assert "ref" in condition and "value" not in condition, (
                    f"{rule['id']}: '{condition['field']}' threshold must use a reference "
                    "dataset (ref), not a hardcoded value"
                )


def test_ref_uses_city_specific_threshold(rent_rule):
    base = {"has_lease": True, "age": 30, "monthly_income": 60000}
    # 臺北 60,000 ≤ 20,744×3 = 62,232 → 收入要件成立
    assert evaluate(rent_rule, {**base, "residence_city": "Taipei"}).status == POSSIBLE
    # 高雄 60,000 > 16,970×3 = 50,910 → 金額不成立，退回追問身分別
    kaohsiung = evaluate(rent_rule, {**base, "residence_city": "Kaohsiung"})
    assert kaohsiung.status == INSUFFICIENT_DATA
    assert "income_status" in kaohsiung.missing_fields


def test_ref_with_unknown_city(rent_rule):
    base = {"has_lease": True, "age": 30}
    # 低於全國最低門檻（15,515×3 = 46,545）→ 任何縣市都成立
    assert evaluate(rent_rule, {**base, "monthly_income": 33333}).status == POSSIBLE
    # 介於最低與最高門檻之間 → 取決於縣市 → 追問 residence_city
    between = evaluate(rent_rule, {**base, "monthly_income": 50000})
    assert between.status == INSUFFICIENT_DATA
    assert "residence_city" in between.missing_fields


def test_missing_dataset_degrades_to_unknown(rent_rule):
    # No reference data at all -> the ref condition is unknown, never a crash.
    result = evaluate(rent_rule, {"has_lease": True, "age": 30, "monthly_income": 33333}, {})
    assert result.status == INSUFFICIENT_DATA
