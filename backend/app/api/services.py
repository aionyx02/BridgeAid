"""Service catalog, source trace, and application-process endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from .. import runtime
from ..service_catalog import service_process_trace, service_source_trace, service_summary

router = APIRouter()


@router.get("/services")
def list_services() -> dict[str, Any]:
    """Source-trace listing: every service with its review status."""
    return {"services": [service_summary(rule) for rule in runtime.rules()]}


@router.get("/services/{service_id}/source")
def service_source(service_id: str) -> dict[str, Any]:
    """Traceable source for one service: official url, version, last_checked_at."""
    rule = runtime.rules_by_id().get(service_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="service not found")
    return service_source_trace(service_id, rule)


@router.get("/services/{service_id}/process")
def service_process(service_id: str) -> dict[str, Any]:
    """Administrative process steps for one service (TASK.014)."""
    rule = runtime.rules_by_id().get(service_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="service not found")
    return service_process_trace(service_id, rule)
