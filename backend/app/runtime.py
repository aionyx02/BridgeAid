"""Process-local runtime dependencies for the FastAPI application.

This module keeps the side-effectful, process-scoped objects in one place:
in-memory stores, the LINE reply adapter, and cached rule/conversation
factories. API routers import this module instead of constructing their own
globals, so new routes can share the same application services explicitly.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from . import config
from .conversation import ConversationManager, InMemorySessionStore, build_intent_parser
from .line.client import LineReplyClient, build_reply_client
from .reminders import InMemoryReminderStore, ReminderService
from .rule_engine import load_rules

session_store = InMemorySessionStore()
reminder_store = InMemoryReminderStore()
reminders = ReminderService(reminder_store)
reply_client: LineReplyClient = build_reply_client()


@lru_cache(maxsize=1)
def rules() -> list[dict[str, Any]]:
    """Load and cache validated service rules once per process."""
    return load_rules()


@lru_cache(maxsize=1)
def rules_by_id() -> dict[str, dict[str, Any]]:
    return {rule["id"]: rule for rule in rules()}


@lru_cache(maxsize=1)
def manager() -> ConversationManager:
    # Parser choice (deterministic vs Ollama, ADR-0004) is fixed at first use.
    parser = build_intent_parser(config.load_settings())
    return ConversationManager(rules(), session_store, parser=parser)
