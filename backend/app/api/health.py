"""Health and runtime-configuration endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from .. import config, runtime

router = APIRouter()


@router.get("/healthz")
def healthz() -> dict[str, Any]:
    settings = config.load_settings()
    return {
        "status": "ok",
        "rules_loaded": len(runtime.rules()),
        "line_configured": settings.line_configured,
        "db_configured": settings.db_configured,
    }
