"""Static Web demo shell is served by FastAPI."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_demo_index_served():
    response = client.get("/demo/")
    assert response.status_code == 200
    assert "BridgeAid Demo" in response.text
    assert "/chat" not in response.text  # endpoint paths live in JS, not visible copy.


def test_demo_assets_served():
    css = client.get("/demo/styles.css")
    js = client.get("/demo/app.js")
    core = client.get("/demo/core.js")
    mark = client.get("/demo/bridgeaid-mark.svg")

    assert css.status_code == 200
    assert "text/css" in css.headers["content-type"]
    assert js.status_code == 200
    assert "javascript" in js.headers["content-type"]
    assert core.status_code == 200
    assert "javascript" in core.headers["content-type"]
    assert mark.status_code == 200
    assert "image/svg+xml" in mark.headers["content-type"]
