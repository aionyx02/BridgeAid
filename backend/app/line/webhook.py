"""LINE webhook signature verification.

LINE signs each webhook request with HMAC-SHA256 over the raw request body,
keyed by the channel secret, base64-encoded in the ``X-Line-Signature`` header.
We verify with the stdlib (no LINE SDK) and use a constant-time compare to avoid
timing leaks (ADR-0003).
"""

from __future__ import annotations

import base64
import hashlib
import hmac


def expected_signature(channel_secret: str, body: bytes) -> str:
    digest = hmac.new(channel_secret.encode("utf-8"), body, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def verify_signature(channel_secret: str, body: bytes, signature: str | None) -> bool:
    """Return True only when the signature matches. Empty secret/signature -> False."""
    if not channel_secret or not signature:
        return False
    return hmac.compare_digest(expected_signature(channel_secret, body), signature)
