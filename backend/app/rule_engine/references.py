"""Reference datasets: annually-updated official figures rules point at.

Policy-derived thresholds (minimum living cost × multiplier, …) must never be
hardcoded into service rules: rules use a ``ref`` condition and the number
lives in ``data/reference/<dataset>.json`` with its validity period and
official sources, schema-validated like every other data contract (ADR-0008).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .loader import DATA_DIR, _read_json

REFERENCE_DIR = DATA_DIR / "reference"
REFERENCE_SCHEMA_PATH = DATA_DIR / "schemas" / "reference-dataset.schema.json"


class ReferenceValidationError(ValueError):
    """Raised when a reference dataset does not satisfy the schema."""


@lru_cache(maxsize=1)
def _validator() -> Draft202012Validator:
    schema = _read_json(REFERENCE_SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def validate_reference(dataset: dict[str, Any]) -> None:
    errors = sorted(_validator().iter_errors(dataset), key=lambda e: list(e.path))
    if errors:
        details = "; ".join(
            f"{'/'.join(map(str, err.path)) or '<root>'}: {err.message}" for err in errors
        )
        raise ReferenceValidationError(details)


def load_reference(path: str | Path) -> dict[str, Any]:
    dataset = _read_json(Path(path))
    validate_reference(dataset)
    return dataset


@lru_cache(maxsize=1)
def load_references(reference_dir: str | Path = REFERENCE_DIR) -> dict[str, dict[str, Any]]:
    """All datasets keyed by id. Cached: reference data is static per process."""
    directory = Path(reference_dir)
    if not directory.is_dir():
        return {}
    datasets = [load_reference(p) for p in sorted(directory.glob("*.json"))]
    return {dataset["id"]: dataset for dataset in datasets}
