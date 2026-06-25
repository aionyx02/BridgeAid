"""Load and schema-validate BridgeAid service rules.

Service rules are untrusted input authored by hand or extracted from public
sources, so every rule is validated against ``service-rule.schema.json`` before
it reaches the evaluator or the database (ADR-0002: human-reviewed, versioned,
source-traceable data).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

# repo_root/backend/app/rule_engine/loader.py -> parents[3] == repo root
REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data"
SCHEMA_PATH = DATA_DIR / "schemas" / "service-rule.schema.json"
SERVICES_DIR = DATA_DIR / "services"


class RuleValidationError(ValueError):
    """Raised when a service rule does not satisfy the schema."""


def _read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=1)
def _validator() -> Draft202012Validator:
    schema = _read_json(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def validate_rule(rule: dict[str, Any]) -> None:
    """Validate a rule against the schema, raising RuleValidationError on failure."""
    errors = sorted(_validator().iter_errors(rule), key=lambda e: list(e.path))
    if errors:
        details = "; ".join(
            f"{'/'.join(map(str, err.path)) or '<root>'}: {err.message}" for err in errors
        )
        raise RuleValidationError(details)


def load_rule(path: str | Path) -> dict[str, Any]:
    """Load and validate a single service-rule JSON file."""
    rule = _read_json(Path(path))
    validate_rule(rule)
    return rule


def load_rules(services_dir: str | Path = SERVICES_DIR) -> list[dict[str, Any]]:
    """Load and validate every ``*.json`` rule in a directory, sorted by id."""
    rules = [load_rule(p) for p in sorted(Path(services_dir).glob("*.json"))]
    return sorted(rules, key=lambda r: r["id"])
