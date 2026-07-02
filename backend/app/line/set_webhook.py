"""Point the LINE channel webhook at a public URL and run LINE's test.

Usage (tunnel URL changes on every ngrok/cloudflared restart)::

    uv run python -m app.line.set_webhook https://<tunnel-host>

`/line/webhook` is appended automatically when the URL has no path. The
channel access token comes from the keychain/env (never printed).
"""

from __future__ import annotations

import sys

import httpx

from .. import config

ENDPOINT_API = "https://api.line.me/v2/bot/channel/webhook/endpoint"
TEST_API = "https://api.line.me/v2/bot/channel/webhook/test"


def normalize_endpoint(url: str) -> str:
    """https required by LINE; default the path to /line/webhook."""
    url = url.strip().rstrip("/")
    if not url.startswith("https://"):
        raise ValueError("webhook endpoint must be https")
    host_and_path = url.removeprefix("https://")
    if "/" not in host_and_path:
        url += "/line/webhook"
    return url


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    try:
        endpoint = normalize_endpoint(sys.argv[1])
    except ValueError as exc:
        print(f"error: {exc}")
        return 2

    settings = config.load_settings()
    if not settings.line_send_configured:
        print("LINE_CHANNEL_ACCESS_TOKEN not configured (keychain/env); aborting")
        return 1

    headers = {"Authorization": f"Bearer {settings.line_channel_access_token}"}
    with httpx.Client(headers=headers, timeout=30.0) as client:
        set_resp = client.put(ENDPOINT_API, json={"endpoint": endpoint})
        set_resp.raise_for_status()
        print(f"webhook endpoint set: {endpoint}")

        test = client.post(TEST_API, json={"endpoint": endpoint}).json()
        print(f"LINE webhook test: success={test.get('success')} status={test.get('statusCode')}")
    return 0 if test.get("success") else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
