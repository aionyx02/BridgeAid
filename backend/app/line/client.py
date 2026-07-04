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
from .flex import results_flex_message

REPLY_URL = "https://api.line.me/v2/bot/message/reply"
PUSH_URL = "https://api.line.me/v2/bot/message/push"


def push_text(access_token: str, to: str, text: str) -> None:
    """Push a plain text message to a LINE user (reminder delivery, ADR-0006)."""
    httpx.post(
        PUSH_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        json={"to": to, "messages": [{"type": "text", "text": text}]},
        timeout=10.0,
    ).raise_for_status()


def reply_to_messages(reply: Reply) -> list[dict[str, Any]]:
    """Render a Reply as LINE messages (text + quick replies + Flex cards)."""
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
    messages: list[dict[str, Any]] = [message]
    flex = results_flex_message(reply.results)
    if flex:
        messages.append(flex)
    return messages


class LineReplyClient(Protocol):
    def reply(self, access_token: str, reply_token: str, reply: Reply) -> None: ...
    def reply_messages(
        self, access_token: str, reply_token: str, messages: list[dict[str, Any]]
    ) -> None: ...


class HttpxLineReplyClient:
    def reply(self, access_token: str, reply_token: str, reply: Reply) -> None:
        self.reply_messages(access_token, reply_token, reply_to_messages(reply))

    def reply_messages(
        self, access_token: str, reply_token: str, messages: list[dict[str, Any]]
    ) -> None:
        httpx.post(
            REPLY_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            json={"replyToken": reply_token, "messages": messages[:5]},  # LINE reply cap
            timeout=10.0,
        )


def build_reply_client() -> LineReplyClient:
    return HttpxLineReplyClient()
