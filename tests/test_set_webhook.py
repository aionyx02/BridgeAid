"""URL normalization for the LINE webhook setup utility."""

from __future__ import annotations

import pytest

from app.line.set_webhook import normalize_endpoint


def test_bare_tunnel_host_gets_webhook_path():
    assert (
        normalize_endpoint("https://example.ngrok-free.dev")
        == "https://example.ngrok-free.dev/line/webhook"
    )


def test_existing_path_is_kept():
    assert normalize_endpoint("https://x.dev/line/webhook") == "https://x.dev/line/webhook"


def test_trailing_slash_is_stripped():
    assert normalize_endpoint("https://x.dev/") == "https://x.dev/line/webhook"


def test_http_is_rejected():
    with pytest.raises(ValueError):
        normalize_endpoint("http://x.dev")
