"""Secret resolution: OS keychain first, environment fallback (ADR-0003)."""

from __future__ import annotations

from app import config


class FakeKeyring:
    def __init__(self, store: dict[tuple[str, str], str]):
        self._store = store

    def get_password(self, service: str, name: str) -> str | None:
        return self._store.get((service, name))


def test_keychain_takes_precedence_over_env(monkeypatch):
    monkeypatch.setattr(
        config, "keyring", FakeKeyring({(config.KEYCHAIN_SERVICE, "K"): "from_keychain"})
    )
    monkeypatch.setenv("K", "from_env")
    assert config.get_secret("K") == "from_keychain"


def test_env_fallback_when_keychain_empty(monkeypatch):
    monkeypatch.setattr(config, "keyring", FakeKeyring({}))
    monkeypatch.setenv("K", "from_env")
    assert config.get_secret("K") == "from_env"


def test_prefixed_env_fallback(monkeypatch):
    monkeypatch.setattr(config, "keyring", FakeKeyring({}))
    monkeypatch.delenv("K", raising=False)
    monkeypatch.setenv("BRIDGEAID_K", "prefixed")
    assert config.get_secret("K") == "prefixed"


def test_missing_secret_returns_none(monkeypatch):
    monkeypatch.setattr(config, "keyring", FakeKeyring({}))
    monkeypatch.delenv("K", raising=False)
    monkeypatch.delenv("BRIDGEAID_K", raising=False)
    assert config.get_secret("K") is None


def test_load_settings_degraded(monkeypatch):
    monkeypatch.setattr(config, "keyring", FakeKeyring({}))
    for key in (config.LINE_CHANNEL_SECRET, config.LINE_CHANNEL_ACCESS_TOKEN, config.DATABASE_URL):
        monkeypatch.delenv(key, raising=False)
        monkeypatch.delenv(f"BRIDGEAID_{key}", raising=False)
    settings = config.load_settings()
    assert settings.line_configured is False
    assert settings.db_configured is False
