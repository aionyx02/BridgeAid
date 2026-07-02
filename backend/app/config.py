"""Configuration and secret loading.

Secrets come from the OS keychain first (Windows Credential Manager via
``keyring``), with an environment-variable fallback for CI/containers
(ADR-0003). Secrets are read into memory on demand and never written to the
repo, logs, or error messages.

Store secrets locally (interactive, value never passed on the command line)::

    uv run keyring set bridgeaid LINE_CHANNEL_SECRET
    uv run keyring set bridgeaid LINE_CHANNEL_ACCESS_TOKEN
    uv run keyring set bridgeaid DATABASE_URL
"""

from __future__ import annotations

import os
from dataclasses import dataclass

try:  # keyring may be unavailable in some headless/CI environments
    import keyring
except Exception:  # pragma: no cover - import guard
    keyring = None  # type: ignore[assignment]

KEYCHAIN_SERVICE = "bridgeaid"

# LINE Messaging API: channel id + channel secret are the channel's basic
# credentials (the secret verifies the webhook signature). The channel access
# token is issued separately and is only needed to call the reply/push API.
LINE_CHANNEL_ID = "LINE_CHANNEL_ID"
LINE_CHANNEL_SECRET = "LINE_CHANNEL_SECRET"
LINE_CHANNEL_ACCESS_TOKEN = "LINE_CHANNEL_ACCESS_TOKEN"
DATABASE_URL = "DATABASE_URL"

# Intent parser selection (ADR-0004). Not secrets, but resolved through the
# same keychain/env lookup so local overrides need no shell profile edits.
INTENT_PARSER = "INTENT_PARSER"  # "ollama" to enable the LLM parser
OLLAMA_HOST = "OLLAMA_HOST"  # default http://localhost:11434
OLLAMA_MODEL = "OLLAMA_MODEL"


def get_secret(name: str) -> str | None:
    """Return a secret by key: OS keychain first, then environment variable.

    Env fallback accepts both ``NAME`` and ``BRIDGEAID_NAME``.
    """
    if keyring is not None:
        try:
            value = keyring.get_password(KEYCHAIN_SERVICE, name)
        except Exception:
            value = None
        if value:
            return value
    return os.environ.get(name) or os.environ.get(f"BRIDGEAID_{name}")


@dataclass(frozen=True)
class Settings:
    """Resolved runtime settings. None means "not configured" (degraded mode)."""

    line_channel_id: str | None
    line_channel_secret: str | None
    line_channel_access_token: str | None
    database_url: str | None
    intent_parser: str | None = None
    ollama_host: str | None = None
    ollama_model: str | None = None

    @property
    def line_configured(self) -> bool:
        """Webhook can verify signatures once the channel secret is present."""
        return bool(self.line_channel_secret)

    @property
    def line_send_configured(self) -> bool:
        """Reply/push API also needs an issued channel access token."""
        return bool(self.line_channel_access_token)

    @property
    def db_configured(self) -> bool:
        return bool(self.database_url)

    @property
    def ollama_intent_enabled(self) -> bool:
        """LLM parser is opt-in; anything else means deterministic (ADR-0004)."""
        return (self.intent_parser or "").strip().lower() == "ollama"


def load_settings() -> Settings:
    """Resolve settings from keychain/env. Cheap; call per request to pick up changes."""
    return Settings(
        line_channel_id=get_secret(LINE_CHANNEL_ID),
        line_channel_secret=get_secret(LINE_CHANNEL_SECRET),
        line_channel_access_token=get_secret(LINE_CHANNEL_ACCESS_TOKEN),
        database_url=get_secret(DATABASE_URL),
        intent_parser=get_secret(INTENT_PARSER),
        ollama_host=get_secret(OLLAMA_HOST),
        ollama_model=get_secret(OLLAMA_MODEL),
    )
