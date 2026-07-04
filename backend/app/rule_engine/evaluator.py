"""Eligibility evaluation for BridgeAid service rules.

Design boundary (ADR-0002): the rule engine — not the LLM — decides eligibility.
Results are explainable: every recommendation carries the conditions it hit and
the fields still missing, and never claims a guaranteed entitlement.

Tri-state logic
---------------
Each condition evaluates to True, False, or None (unknown, because a needed
field is absent from the profile). Unknowns propagate so the engine can return
``insufficient_data`` instead of guessing:

- ``all``: any False -> False; else any None -> None; else True
- ``any``: any True  -> True;  else any None -> None; else False

Root mapping: True -> ``possible``, None -> ``insufficient_data``,
False -> ``unlikely``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .operators import apply_operator
from .references import load_references

POSSIBLE = "possible"
INSUFFICIENT_DATA = "insufficient_data"
UNLIKELY = "unlikely"

Profile = dict[str, Any]
References = dict[str, dict[str, Any]]


@dataclass
class Evaluation:
    """Explainable result of evaluating one service rule against a profile."""

    service_id: str
    service_name: str
    status: str
    hit_conditions: list[dict[str, Any]] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)
    documents: list[str] = field(default_factory=list)
    needs_review: bool = False
    source: dict[str, Any] = field(default_factory=dict)


def _ref_thresholds(
    ref: dict[str, Any], profile: Profile, references: References
) -> tuple[list[Any] | None, set[str]]:
    """Candidate threshold(s) for a ``ref`` condition (ADR-0008).

    Rules never hardcode policy-derived numbers; they name a dataset in
    ``data/reference/`` and the threshold is resolved here. When the selector
    field (e.g. residence_city) is unknown, every possible threshold is
    returned so the caller can tell decided-everywhere apart from "depends on
    the selector" — the latter blocks on the selector field.
    """
    dataset = references.get(ref["dataset"])
    if dataset is None:
        return None, set()
    multiplier = ref.get("multiplier", 1)
    selector = ref.get("by")
    if not selector:
        return [dataset["default"] * multiplier], set()
    key = profile.get(selector)
    if key is not None:
        return [dataset["values"].get(key, dataset["default"]) * multiplier], set()
    candidates = {dataset["default"], *dataset["values"].values()}
    return sorted(value * multiplier for value in candidates), {selector}


def _eval_condition(
    condition: dict[str, Any],
    profile: Profile,
    *,
    hits: list[dict[str, Any]],
    references: References,
) -> tuple[bool | None, set[str]]:
    """Return (state, blocking_fields). A leaf blocks on its own field if unknown."""
    field_name = condition["field"]
    operator = condition["operator"]

    if operator == "exists":
        present = field_name in profile and profile[field_name] is not None
        if present:
            hits.append(condition)
        return present, set()

    if field_name not in profile or profile[field_name] is None:
        return None, {field_name}

    if "ref" in condition:
        thresholds, selector_fields = _ref_thresholds(condition["ref"], profile, references)
        if thresholds is None:  # dataset missing/unloadable -> cannot decide
            return None, {field_name}
        outcomes = {apply_operator(operator, profile[field_name], t) for t in thresholds}
        if len(outcomes) > 1:  # decision depends on the unknown selector
            return None, selector_fields
        result = outcomes.pop()
        if result:
            hits.append(condition)
        return result, set()

    result = apply_operator(operator, profile[field_name], condition.get("value"))
    if result:
        hits.append(condition)
    return result, set()


def _eval_node(
    node: dict[str, Any],
    profile: Profile,
    *,
    hits: list[dict[str, Any]],
    references: References,
) -> tuple[bool | None, set[str]]:
    """Tri-state evaluation that reports only the fields that actually block.

    A field is "missing" only when its unknown value is what keeps the node from
    resolving. Once a group is already decided (an ``all`` failed, or an ``any``
    matched), unknown sibling branches are irrelevant and are not reported.
    """
    if "all" in node or "any" in node:
        mode = "all" if "all" in node else "any"
        children = [
            _eval_node(child, profile, hits=hits, references=references) for child in node[mode]
        ]

        if mode == "all":
            if any(state is False for state, _ in children):
                return False, set()
            if any(state is None for state, _ in children):
                blocking = set().union(*(m for state, m in children if state is None))
                return None, blocking
            return True, set()

        # any
        if any(state is True for state, _ in children):
            return True, set()
        if any(state is None for state, _ in children):
            blocking = set().union(*(m for state, m in children if state is None))
            return None, blocking
        return False, set()

    return _eval_condition(node, profile, hits=hits, references=references)


def build_document_checklist(
    rule: dict[str, Any], profile: Profile, references: References | None = None
) -> list[str]:
    """Documents that apply to this profile.

    Includes a document when its condition is ``always``, or when its condition
    evaluates True. A condition whose field is still unknown is included too, so
    the user is not told to skip a document we cannot yet rule out.
    """
    resolved = load_references() if references is None else references
    checklist: list[str] = []
    for doc in rule.get("required_documents", []):
        condition = doc["condition"]
        if condition == "always":
            checklist.append(doc["name"])
            continue
        outcome, _ = _eval_condition(condition, profile, hits=[], references=resolved)
        if outcome is True or outcome is None:
            checklist.append(doc["name"])
    return checklist


def evaluate(
    rule: dict[str, Any], profile: Profile, references: References | None = None
) -> Evaluation:
    """Evaluate one service rule against a citizen profile.

    ``references`` defaults to the bundled ``data/reference`` datasets; pass
    ``{}`` to evaluate with no reference data (ref conditions become unknown).
    """
    resolved = load_references() if references is None else references
    hits: list[dict[str, Any]] = []
    outcome, missing = _eval_node(
        rule["eligibility_rules"], profile, hits=hits, references=resolved
    )

    if outcome is True:
        status = POSSIBLE
    elif outcome is None:
        status = INSUFFICIENT_DATA
    else:
        status = UNLIKELY

    return Evaluation(
        service_id=rule["id"],
        service_name=rule["name"],
        status=status,
        hit_conditions=hits,
        missing_fields=sorted(missing),
        documents=build_document_checklist(rule, profile, resolved),
        needs_review=rule.get("status") == "needs_review",
        source=rule.get("source", {}),
    )


def evaluate_all(
    rules: list[dict[str, Any]], profile: Profile, references: References | None = None
) -> list[Evaluation]:
    """Evaluate every rule, ranking ``possible`` first, then insufficient data."""
    order = {POSSIBLE: 0, INSUFFICIENT_DATA: 1, UNLIKELY: 2}
    resolved = load_references() if references is None else references
    results = [evaluate(rule, profile, resolved) for rule in rules]
    return sorted(results, key=lambda e: (order[e.status], e.service_id))


def detect_conflicts(
    selected_ids: list[str], rules_by_id: dict[str, dict[str, Any]]
) -> list[dict[str, str]]:
    """Find conflicts among selected services (e.g. same event, non-combinable).

    Returns each conflicting pair once, with the declared type and reason.
    """
    selected = set(selected_ids)
    seen: set[frozenset[str]] = set()
    conflicts: list[dict[str, str]] = []
    for service_id in selected_ids:
        rule = rules_by_id.get(service_id)
        if not rule:
            continue
        for conflict in rule.get("conflicts", []):
            other = conflict["service_id"]
            if other not in selected:
                continue
            pair = frozenset({service_id, other})
            if pair in seen:
                continue
            seen.add(pair)
            conflicts.append(
                {
                    "service_ids": sorted(pair),
                    "type": conflict["type"],
                    "reason": conflict["reason"],
                }
            )
    return conflicts
