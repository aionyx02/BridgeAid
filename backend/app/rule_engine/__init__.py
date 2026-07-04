"""BridgeAid rule engine.

The rule engine evaluates verifiable, versioned service rules to decide
eligibility. AI handles intent/field extraction only; eligibility decisions
live here (ADR-0002).
"""

from .evaluator import (
    INSUFFICIENT_DATA,
    POSSIBLE,
    UNLIKELY,
    Evaluation,
    build_document_checklist,
    detect_conflicts,
    evaluate,
    evaluate_all,
)
from .loader import RuleValidationError, load_rule, load_rules, validate_rule
from .references import (
    ReferenceValidationError,
    load_reference,
    load_references,
    validate_reference,
)

__all__ = [
    "POSSIBLE",
    "INSUFFICIENT_DATA",
    "UNLIKELY",
    "Evaluation",
    "evaluate",
    "evaluate_all",
    "build_document_checklist",
    "detect_conflicts",
    "load_rule",
    "load_rules",
    "validate_rule",
    "RuleValidationError",
    "load_reference",
    "load_references",
    "validate_reference",
    "ReferenceValidationError",
]
