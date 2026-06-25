"""LINE reply client (Messaging API).

A port so the webhook can be tested without network. The default httpx client
calls the reply endpoint with the channel access token (issued separately from
the channel id/secret). Sending is skipped when no access token is configured
(degraded mode, ADR-0003).
"""

from __future__ import annotations

from typing import Any, Protocol

import httpx

from ..conversation import Reply

REPLY_URL = "https://api.line.me/v2/bot/message/reply"


def reply_to_messages(reply: Reply) -> list[dict[str, Any]]:
    """Render a Reply as LINE message objects (text + quick-reply buttons)."""
    message: dict[str, Any] = {"type": "text", "text": reply.text}
    if reply.options:
        message["quickReply"] = {
            "items": [
                {
                    "type": "action",
                    "action": {"type": "message", "label": option[:20], "text": option},
                }
                for option in reply.options[:13]  # LINE allows up to 13 quick-reply items
            ]
        }
    return [message]


class LineReplyClient(Protocol):
    def reply(self, access_token: str, reply_token: str, reply: Reply) -> None: ...


class HttpxLineReplyClient:
    def reply(self, access_token: str, reply_token: str, reply: Reply) -> None:
        httpx.post(
            REPLY_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            json={"replyToken": reply_token, "messages": reply_to_messages(reply)},
            timeout=10.0,
        )


def build_reply_client() -> LineReplyClient:
    return HttpxLineReplyClient()
