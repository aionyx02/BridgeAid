"""Recommendation endpoints."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter

from .. import runtime
from ..recommendation import build_recommendation
from ..rule_engine import evaluate_all
from .schemas import RecommendRequest

router = APIRouter()


@router.post("/recommend")
def recommend(request: RecommendRequest) -> dict[str, Any]:
    """Return explainable recommendations. AI never decides eligibility here."""
    evaluations = evaluate_all(runtime.rules(), request.profile)
    recommendation = build_recommendation(evaluations, runtime.rules_by_id())
    return {
        "results": [asdict(result) for result in evaluations],
        "conflicts": recommendation.conflicts,
        "document_checklist": recommendation.document_checklist,
    }
