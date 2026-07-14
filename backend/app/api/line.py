"""LINE webhook transport endpoint."""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Request

from .. import config, runtime
from ..line.reminder_flow import handle_postback
from ..line.webhook import verify_signature

router = APIRouter(prefix="/line")


@router.post("/webhook")
async def line_webhook(request: Request) -> dict[str, str]:
    settings = config.load_settings()
    if not settings.line_configured:
        raise HTTPException(status_code=503, detail="LINE webhook not configured")

    body = await request.body()
    signature = request.headers.get("X-Line-Signature")
    if not verify_signature(settings.line_channel_secret or "", body, signature):
        raise HTTPException(status_code=401, detail="invalid signature")

    try:
        payload = json.loads(body or b"{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="invalid JSON payload") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="invalid JSON payload")

    manager = runtime.manager()
    for event in payload.get("events", []):
        reply_token = event.get("replyToken")
        source = event.get("source") or {}
        session_id = source.get("userId") or reply_token or ""

        if event.get("type") == "postback":
            messages = handle_postback(
                session_id,
                event.get("postback", {}).get("data", ""),
                runtime.rules_by_id(),
                runtime.reminders,
            )
            if messages and settings.line_send_configured and reply_token:
                runtime.reply_client.reply_messages(
                    settings.line_channel_access_token or "", reply_token, messages
                )
            continue

        if event.get("type") != "message" or event.get("message", {}).get("type") != "text":
            continue
        reply = manager.handle_message(session_id, event["message"]["text"], channel="line")
        if settings.line_send_configured and reply_token:
            runtime.reply_client.reply(settings.line_channel_access_token or "", reply_token, reply)

    return {"status": "ok"}
