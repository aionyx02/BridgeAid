"""BridgeAid FastAPI application entrypoint.

Runs without a database or LINE secret (degraded mode, ADR-0003):
- ``GET  /healthz``       liveness + what is configured
- ``POST /recommend``     rule-engine recommendations (no DB needed)
- ``POST /chat``          conversational entry (Web): one turn per request
- ``POST /line/webhook``  signature-verified LINE events -> same conversation

Local daemon:  ``uv run uvicorn app.main:app --reload``
"""

from __future__ import annotations

from . import config
from .factory import create_app

app = create_app()

__all__ = ["app", "config", "create_app"]
