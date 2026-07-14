"""FastAPI application factory."""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import runtime
from .api import register_api_routes
from .reminder_delivery import LineOrLogSender, run_scheduler

DEMO_DIR = Path(__file__).resolve().parents[2] / "demo"


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Run the reminder delivery sweep for the app's lifetime (ADR-0006)."""
    scheduler = asyncio.create_task(run_scheduler(runtime.reminder_store, LineOrLogSender()))
    try:
        yield
    finally:
        scheduler.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await scheduler


def create_app() -> FastAPI:
    """Build the HTTP application and attach all transport routes."""
    app = FastAPI(
        title="BridgeAid",
        summary="Proactive Public Service Navigator",
        lifespan=lifespan,
    )
    register_api_routes(app)
    app.mount("/demo", StaticFiles(directory=DEMO_DIR, html=True), name="demo")
    return app
