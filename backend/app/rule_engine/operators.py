"""Comparison operators for eligibility conditions.

Operators are pure functions over (actual, expected). Field presence and the
tri-state (true/false/unknown) logic live in the evaluator; operators only run
once a value is known. No ``eval`` and no dynamic code: the operator set is a
fixed allowlist, which keeps rule data untrusted-input-safe.
"""

from __future__ import annotations

from collections.abc import Callable
from numbers import Real
from typing import Any


def _as_number(value: Any) -> Real | None:
    """Return value as a real number, or None if it is not comparable."""
    if isinstance(value, bool):  # bool is a subclass of int; exclude it explicitly
        return None
    if isinstance(value, Real):
        return value
    return None


def _numeric(actual: Any, expected: Any, compare: Callable[[Real, Real], bool]) -> bool:
    a, b = _as_number(actual), _as_number(expected)
    if a is None or b is None:
        return False
    return compare(a, b)


def _ensure_iterable(expected: Any) -> tuple:
    return tuple(expected) if isinstance(expected, (list, tuple, set)) else (expected,)


# Operators that require an "expected" value. "exists" is handled by the
# evaluator because it depends on presence, not on a value comparison.
OPERATORS: dict[str, Callable[[Any, Any], bool]] = {
    "equals": lambda actual, expected: actual == expected,
    "not_equals": lambda actual, expected: actual != expected,
    "in": lambda actual, expected: actual in _ensure_iterable(expected),
    "not_in": lambda actual, expected: actual not in _ensure_iterable(expected),
    "gt": lambda actual, expected: _numeric(actual, expected, lambda a, b: a > b),
    "gte": lambda actual, expected: _numeric(actual, expected, lambda a, b: a >= b),
    "lt": lambda actual, expected: _numeric(actual, expected, lambda a, b: a < b),
    "lte": lambda actual, expected: _numeric(actual, expected, lambda a, b: a <= b),
}


def apply_operator(operator: str, actual: Any, expected: Any) -> bool:
    """Apply a value operator. Raises ValueError for unknown operators."""
    try:
        return OPERATORS[operator](actual, expected)
    except KeyError:
        raise ValueError(f"unsupported value operator: {operator!r}") from None
