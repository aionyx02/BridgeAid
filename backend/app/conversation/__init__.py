"""Conversation layer: intent extraction, session state, follow-up questions.

AI is the entry/translation layer (ADR-0002): this package extracts profile
fields from natural language and drives follow-up questions, but eligibility is
always decided by the rule engine. The intent parser is a port
(`IntentParser`); the default is deterministic (keyword-based, no LLM/key), and
an LLM adapter can be swapped in later.
"""

from .intent import DeterministicIntentParser, IntentParser
from .manager import (
    MAX_QUESTIONS,
    ConversationManager,
    InMemorySessionStore,
    Reply,
    Session,
    SessionStore,
)

__all__ = [
    "IntentParser",
    "DeterministicIntentParser",
    "ConversationManager",
    "InMemorySessionStore",
    "SessionStore",
    "Session",
    "Reply",
    "MAX_QUESTIONS",
]
