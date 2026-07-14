"""Ollama LLM intent parser (ADR-0004): whitelist wash + deterministic fallback."""

from __future__ import annotations

import json

import httpx

from app.config import Settings
from app.conversation import (
    DeterministicIntentParser,
    OllamaIntentParser,
    build_intent_parser,
)


def _parser_returning(content: dict | str) -> OllamaIntentParser:
    """Parser whose mocked Ollama always answers with `content`."""
    body = content if isinstance(content, str) else json.dumps(content)

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/chat"
        payload = json.loads(request.content)
        assert payload["stream"] is False
        assert payload["think"] is False  # thinking would blow the latency budget
        return httpx.Response(200, json={"message": {"role": "assistant", "content": body}})

    return OllamaIntentParser(client=httpx.Client(transport=httpx.MockTransport(handler)))


def _failing_parser(exc: Exception | None = None, status: int = 500) -> OllamaIntentParser:
    def handler(request: httpx.Request) -> httpx.Response:
        if exc is not None:
            raise exc
        return httpx.Response(status)

    return OllamaIntentParser(client=httpx.Client(transport=httpx.MockTransport(handler)))


def test_valid_llm_fields_are_extracted():
    parser = _parser_returning(
        {"residence_city": "Taipei", "event_type": "unemployment", "has_lease": True, "age": 40}
    )
    profile = parser.extract("我沒頭路了，住天龍國，厝是用租的，今年四十")
    assert profile == {
        "residence_city": "Taipei",
        "event_type": "unemployment",
        "has_lease": True,
        "age": 40,
    }


def test_hallucinated_fields_and_invalid_tokens_are_washed():
    parser = _parser_returning(
        {
            "residence_city": "Tokyo",  # not a supported city token
            "event_type": "divorce",  # not a canonical event
            "income_status": "low_income",  # certified status: LLM may never set it
            "has_lease": False,  # booleans may only be set True
            "caregiver": "yes",  # wrong type
            "age": 500,  # out of range
            "national_id": "A123456789",  # never whitelisted
        }
    )
    assert parser.extract("隨便講講") == {}


def test_fields_without_text_evidence_are_dropped():
    # Model invents an age and a lease for a text that mentions neither.
    parser = _parser_returning({"event_type": "death_in_family", "age": 35, "has_lease": True})
    assert parser.extract("阿公上個月走了") == {"event_type": "death_in_family"}


def test_fields_with_text_evidence_pass_the_gate():
    parser = _parser_returning({"age": 42, "has_lease": True})
    profile = parser.extract("我四十二歲，租厝住")
    assert profile == {"age": 42, "has_lease": True}


def test_deterministic_keywords_win_over_llm_output():
    # LLM says Kaohsiung, but the text plainly says 台北 -> keyword match wins.
    parser = _parser_returning({"residence_city": "Kaohsiung"})
    assert parser.extract("我住台北")["residence_city"] == "Taipei"


def test_llm_widens_coverage_beyond_keywords():
    # No keyword for "被公司趕出來" -> deterministic alone finds nothing.
    parser = _parser_returning({"event_type": "unemployment"})
    assert DeterministicIntentParser().extract("我被公司趕出來了") == {}
    assert parser.extract("我被公司趕出來了") == {"event_type": "unemployment"}


def test_connection_error_falls_back_to_deterministic():
    parser = _failing_parser(exc=httpx.ConnectError("refused"))
    assert parser.extract("我失業了，住台北") == {
        "event_type": "unemployment",
        "residence_city": "Taipei",
    }


def test_timeout_falls_back_to_deterministic():
    parser = _failing_parser(exc=httpx.ReadTimeout("slow"))
    assert parser.extract("台北租屋")["has_lease"] is True


def test_http_error_falls_back_to_deterministic():
    parser = _failing_parser(status=500)
    assert parser.extract("我失業了")["event_type"] == "unemployment"


def test_non_json_content_falls_back_to_deterministic():
    parser = _parser_returning("抱歉，我不確定。")
    assert parser.extract("我失業了")["event_type"] == "unemployment"


def test_failure_cooldown_skips_ollama_after_timeout():
    calls = 0
    now = 0.0

    def clock() -> float:
        return now

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout("slow")

    parser = OllamaIntentParser(
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        cooldown_seconds=60.0,
        clock=clock,
    )

    assert parser.extract("台北租屋") == {"residence_city": "Taipei", "has_lease": True}
    assert calls == 1

    assert parser.extract("我失業了") == {"event_type": "unemployment"}
    assert calls == 1


def _settings(**overrides) -> Settings:
    values = dict(
        line_channel_id=None,
        line_channel_secret=None,
        line_channel_access_token=None,
        database_url=None,
    )
    values.update(overrides)
    return Settings(**values)


def test_parser_defaults_to_deterministic():
    assert isinstance(build_intent_parser(_settings()), DeterministicIntentParser)


def test_parser_opt_in_via_settings():
    parser = build_intent_parser(_settings(intent_parser="ollama"))
    assert isinstance(parser, OllamaIntentParser)


def test_unrelated_intent_parser_value_stays_deterministic():
    assert isinstance(
        build_intent_parser(_settings(intent_parser="cloud")), DeterministicIntentParser
    )
