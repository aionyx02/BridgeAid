"""Import validated service rules into a persistence backend.

The transform (`rule_to_rows`) is pure and unit-tested; the actual write goes
through a `ServiceRepository` port so the domain stays decoupled from the DB
driver (ADR-0003). Rules are validated by the loader before they get here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from .rule_engine import load_rules


@dataclass
class ServiceRows:
    """Normalized rows for one service, ready for persistence."""

    service: dict[str, Any]
    source: dict[str, Any]
    version: dict[str, Any]
    eligibility: dict[str, Any]
    documents: list[dict[str, Any]] = field(default_factory=list)
    conflicts: list[dict[str, Any]] = field(default_factory=list)


@runtime_checkable
class ServiceRepository(Protocol):
    """Persistence port. Implementations decide storage (e.g. PostgreSQL)."""

    def save(self, rows: ServiceRows) -> None: ...


def rule_to_rows(rule: dict[str, Any]) -> ServiceRows:
    """Transform a validated service rule into normalized persistence rows."""
    service_id = rule["id"]
    version = rule["version"]
    area = rule.get("area", {})
    return ServiceRows(
        service={
            "id": service_id,
            "name": rule["name"],
            "category": rule["category"],
            "jurisdiction": rule["jurisdiction"],
            "status": rule.get("status", "active"),
            "area_type": area.get("type"),
            "area_value": area.get("value"),
        },
        source=dict(rule["source"]),
        version={
            "service_id": service_id,
            "version": version,
            "review_status": rule.get("status", "active"),
        },
        eligibility={
            "service_id": service_id,
            "version": version,
            "rule_jsonb": rule["eligibility_rules"],
        },
        documents=[
            {
                "service_id": service_id,
                "document_name": doc["name"],
                "condition_jsonb": doc["condition"],
            }
            for doc in rule.get("required_documents", [])
        ],
        conflicts=[
            {
                "service_id": service_id,
                "conflict_service_id": conflict["service_id"],
                "conflict_type": conflict["type"],
                "reason": conflict["reason"],
            }
            for conflict in rule.get("conflicts", [])
        ],
    )


@dataclass
class ImportSummary:
    services: int = 0
    documents: int = 0
    conflicts: int = 0


def import_rules(rules: list[dict[str, Any]], repo: ServiceRepository) -> ImportSummary:
    """Persist every rule through the repository and return counts."""
    summary = ImportSummary()
    for rule in rules:
        rows = rule_to_rows(rule)
        repo.save(rows)
        summary.services += 1
        summary.documents += len(rows.documents)
        summary.conflicts += len(rows.conflicts)
    return summary


def main() -> int:
    """CLI entry: import bundled rules into the configured database."""
    from . import config

    settings = config.load_settings()
    if not settings.db_configured:
        print(
            "DATABASE_URL not configured. Set it via:\n"
            "  uv run keyring set bridgeaid DATABASE_URL\n"
            "or export DATABASE_URL. Skipping import."
        )
        return 0

    from .db import PostgresServiceRepository, connect

    rules = load_rules()
    with connect(settings.database_url) as conn:  # type: ignore[arg-type]
        repo = PostgresServiceRepository(conn)
        summary = import_rules(rules, repo)
        conn.commit()
    print(
        f"imported {summary.services} services, "
        f"{summary.documents} documents, {summary.conflicts} conflicts"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
