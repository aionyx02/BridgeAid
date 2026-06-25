"""LINE webhook HMAC-SHA256 signature verification."""

from __future__ import annotations

from app.line.webhook import expected_signature, verify_signature

SECRET = "test_channel_secret"
BODY = b'{"events":[],"destination":"x"}'


def test_valid_signature_passes():
    signature = expected_signature(SECRET, BODY)
    assert verify_signature(SECRET, BODY, signature) is True


def test_tampered_body_fails():
    signature = expected_signature(SECRET, BODY)
    assert verify_signature(SECRET, BODY + b"!", signature) is False


def test_wrong_secret_fails():
    signature = expected_signature(SECRET, BODY)
    assert verify_signature("other_secret", BODY, signature) is False


def test_missing_signature_or_secret_fails():
    assert verify_signature(SECRET, BODY, None) is False
    assert verify_signature("", BODY, expected_signature(SECRET, BODY)) is False
