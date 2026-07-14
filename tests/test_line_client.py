"""LINE client adapter behavior."""

from __future__ import annotations

import httpx
import pytest

from app.line.client import HttpxLineReplyClient


def test_reply_messages_raises_for_http_errors(monkeypatch):
    def fake_post(*args, **kwargs):
        return httpx.Response(500, request=httpx.Request("POST", "https://line.example/reply"))

    monkeypatch.setattr("app.line.client.httpx.post", fake_post)

    with pytest.raises(httpx.HTTPStatusError):
        HttpxLineReplyClient().reply_messages(
            "token",
            "reply-token",
            [{"type": "text", "text": "hi"}],
        )
