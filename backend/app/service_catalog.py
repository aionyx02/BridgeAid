"""Pure mappers for service catalog API responses."""

from __future__ import annotations

from typing import Any


def service_summary(rule: dict[str, Any]) -> dict[str, Any]:
    """Compact service listing item with policy-review status."""
    return {
        "service_id": rule["id"],
        "name": rule["name"],
        "category": rule["category"],
        "status": rule.get("status", "active"),
        "needs_review": rule.get("status") == "needs_review",
    }


def service_source_trace(service_id: str, rule: dict[str, Any]) -> dict[str, Any]:
    """Traceable source payload for one service."""
    return {
        "service_id": service_id,
        "service_name": rule["name"],
        "version": rule["version"],
        "status": rule.get("status", "active"),
        "needs_review": rule.get("status") == "needs_review",
        "source": rule["source"],
    }


def service_process_trace(service_id: str, rule: dict[str, Any]) -> dict[str, Any]:
    """Administrative process payload for one service."""
    return {
        "service_id": service_id,
        "service_name": rule["name"],
        "steps": rule.get("application_process", []),
        "version": rule["version"],
        "needs_review": rule.get("status") == "needs_review",
        "source": rule["source"],
    }
