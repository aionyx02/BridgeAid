"""PostgreSQL persistence (psycopg v3).

Imported lazily — only when ``DATABASE_URL`` is configured — so the API and the
importer transform run without a database (ADR-0003: degraded mode). Implements
the `ServiceRepository` port from `importer`.
"""

from __future__ import annotations

from typing import Any

import psycopg
from psycopg.types.json import Json

from .importer import ServiceRows


def connect(database_url: str) -> psycopg.Connection:
    """Open a PostgreSQL connection. Caller manages the transaction/commit."""
    return psycopg.connect(database_url)


class PostgresServiceRepository:
    """Idempotent upserts for a single service and its related rows."""

    def __init__(self, conn: psycopg.Connection) -> None:
        self._conn = conn

    def save(self, rows: ServiceRows) -> None:
        with self._conn.cursor() as cur:
            source_id = self._upsert_source(cur, rows.source)
            self._upsert_service(cur, rows.service)
            self._upsert_version(cur, rows.version)
            self._replace_eligibility(cur, rows.eligibility, source_id)
            self._replace_documents(cur, rows.service["id"], rows.documents)
            self._replace_conflicts(cur, rows.service["id"], rows.conflicts)

    @staticmethod
    def _upsert_source(cur: psycopg.Cursor, source: dict[str, Any]) -> int:
        cur.execute(
            """
            INSERT INTO source_documents (title, url, publisher, last_checked_at)
            VALUES (%(title)s, %(url)s, %(publisher)s, %(last_checked_at)s)
            ON CONFLICT (url) DO UPDATE
                SET title = EXCLUDED.title,
                    publisher = EXCLUDED.publisher,
                    last_checked_at = EXCLUDED.last_checked_at
            RETURNING id
            """,
            {"publisher": None, **source},
        )
        return cur.fetchone()[0]

    @staticmethod
    def _upsert_service(cur: psycopg.Cursor, service: dict[str, Any]) -> None:
        cur.execute(
            """
            INSERT INTO services (id, name, category, jurisdiction, status, area_type, area_value)
            VALUES (%(id)s, %(name)s, %(category)s, %(jurisdiction)s, %(status)s,
                    %(area_type)s, %(area_value)s)
            ON CONFLICT (id) DO UPDATE
                SET name = EXCLUDED.name,
                    category = EXCLUDED.category,
                    jurisdiction = EXCLUDED.jurisdiction,
                    status = EXCLUDED.status,
                    area_type = EXCLUDED.area_type,
                    area_value = EXCLUDED.area_value
            """,
            service,
        )

    @staticmethod
    def _upsert_version(cur: psycopg.Cursor, version: dict[str, Any]) -> None:
        cur.execute(
            """
            INSERT INTO service_versions (service_id, version, review_status)
            VALUES (%(service_id)s, %(version)s, %(review_status)s)
            ON CONFLICT (service_id, version) DO UPDATE
                SET review_status = EXCLUDED.review_status
            """,
            version,
        )

    @staticmethod
    def _replace_eligibility(
        cur: psycopg.Cursor, eligibility: dict[str, Any], source_id: int
    ) -> None:
        cur.execute(
            "DELETE FROM eligibility_rules WHERE service_id = %(service_id)s "
            "AND version = %(version)s",
            eligibility,
        )
        cur.execute(
            """
            INSERT INTO eligibility_rules (service_id, version, rule_jsonb, source_id)
            VALUES (%(service_id)s, %(version)s, %(rule_jsonb)s, %(source_id)s)
            """,
            {
                "service_id": eligibility["service_id"],
                "version": eligibility["version"],
                "rule_jsonb": Json(eligibility["rule_jsonb"]),
                "source_id": source_id,
            },
        )

    @staticmethod
    def _replace_documents(
        cur: psycopg.Cursor, service_id: str, documents: list[dict[str, Any]]
    ) -> None:
        cur.execute("DELETE FROM required_documents WHERE service_id = %s", (service_id,))
        for doc in documents:
            cur.execute(
                """
                INSERT INTO required_documents (service_id, document_name, condition_jsonb)
                VALUES (%(service_id)s, %(document_name)s, %(condition_jsonb)s)
                """,
                {**doc, "condition_jsonb": Json(doc["condition_jsonb"])},
            )

    @staticmethod
    def _replace_conflicts(
        cur: psycopg.Cursor, service_id: str, conflicts: list[dict[str, Any]]
    ) -> None:
        cur.execute("DELETE FROM conflict_rules WHERE service_id = %s", (service_id,))
        for conflict in conflicts:
            cur.execute(
                """
                INSERT INTO conflict_rules
                    (service_id, conflict_service_id, conflict_type, reason)
                VALUES (%(service_id)s, %(conflict_service_id)s, %(conflict_type)s, %(reason)s)
                """,
                conflict,
            )
