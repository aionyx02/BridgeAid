"""Aggregate per-service evaluations into a user-facing recommendation.

Takes the rule engine's evaluations and produces (a) the services that possibly
qualify, (b) conflicts among them (e.g. choose-one), and (c) a de-duplicated
document checklist that records which services need each document. Pure and
reused by both /recommend and /chat (TASK.005).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .rule_engine import POSSIBLE, Evaluation, detect_conflicts


@dataclass
class Recommendation:
    possible: list[dict[str, Any]] = field(default_factory=list)
    conflicts: list[dict[str, Any]] = field(default_factory=list)
    document_checklist: list[dict[str, Any]] = field(default_factory=list)


def aggregate_documents(possible: list[Evaluation]) -> list[dict[str, Any]]:
    """Merge document checklists across services, preserving first-seen order.

    Each entry is ``{document, services}`` so the UI can show one combined,
    checkable list while still attributing each document to its services.
    """
    order: list[str] = []
    by_document: dict[str, list[str]] = {}
    for evaluation in possible:
        for document in evaluation.documents:
            if document not in by_document:
                by_document[document] = []
                order.append(document)
            by_document[document].append(evaluation.service_id)
    return [{"document": name, "services": by_document[name]} for name in order]


def build_recommendation(
    evaluations: list[Evaluation], rules_by_id: dict[str, dict[str, Any]]
) -> Recommendation:
    """Build conflicts + merged checklist over the services that possibly qualify."""
    possible = [e for e in evaluations if e.status == POSSIBLE]
    conflicts = detect_conflicts([e.service_id for e in possible], rules_by_id)
    return Recommendation(
        possible=[asdict(e) for e in possible],
        conflicts=conflicts,
        document_checklist=aggregate_documents(possible),
    )
