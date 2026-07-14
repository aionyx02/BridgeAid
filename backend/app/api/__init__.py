"""FastAPI router registration for BridgeAid."""

from __future__ import annotations

from fastapi import FastAPI

from . import chat, health, line, recommendations, reminders, services

_ROUTERS = (
    health.router,
    recommendations.router,
    chat.router,
    reminders.router,
    services.router,
    line.router,
)


def register_api_routes(app: FastAPI) -> None:
    """Attach every API router to the app.

    New feature areas should add their router here and keep endpoint handlers
    in a focused module instead of growing ``app.main``.
    """
    for router in _ROUTERS:
        app.include_router(router)
