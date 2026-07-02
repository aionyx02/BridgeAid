"""LLM intent/field extraction via a local Ollama instance (ADR-0004).

`OllamaIntentParser` implements the same `IntentParser` port as
`DeterministicIntentParser`. The model only extracts fields — eligibility is
always the rule engine's call. Its output is treated as untrusted input: every
field goes through a whitelist + type/enum wash before it may touch a profile,
and the deterministic keyword parser's hits always win on conflict, so LLM
output can widen coverage but never override a high-precision keyword match.

If Ollama is unreachable, slow, or returns garbage, extraction silently falls
back to the deterministic parser — the conversation is never blocked.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from ..config import Settings
from .intent import DeterministicIntentParser, IntentParser

logger = logging.getLogger(__name__)

DEFAULT_HOST = "http://localhost:11434"
DEFAULT_MODEL = "qwen3:4b"
# Local single-turn extraction; fail fast so the fallback keeps the chat snappy.
TIMEOUT = httpx.Timeout(10.0, connect=2.0)

# Canonical profile tokens (docs/data.md). Anything outside these is dropped.
_ENUM_FIELDS: dict[str, frozenset[str]] = {
    "residence_city": frozenset({"Taipei", "Kaohsiung"}),
    "event_type": frozenset(
        {"unemployment", "illness", "fire", "major_accident", "death_in_family"}
    ),
    "income_status": frozenset({"low_income", "mid_low_income", "near_threshold", "general"}),
}
# Booleans follow the deterministic parser's rule: only ever set True, never
# guess False, so unknown fields stay unknown and can still be asked.
_BOOL_FIELDS = frozenset({"has_lease", "caregiver", "care_need", "employment_insured"})
_AGE_RANGE = range(1, 121)

# Structured-output schema sent to Ollama (`format`), mirroring the whitelist.
_FORMAT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        **{
            field: {"type": "string", "enum": sorted(values)}
            for field, values in _ENUM_FIELDS.items()
        },
        **{field: {"type": "boolean"} for field in sorted(_BOOL_FIELDS)},
        "age": {"type": "integer"},
    },
    "additionalProperties": False,
}

_SYSTEM_PROMPT = """\
你是台灣公共服務導航系統的欄位抽取器。從使用者敘述中抽取欄位，輸出 JSON。
規則：
- 只在敘述有明確正面證據時才輸出該欄位；不確定就省略，絕不猜測。
- 布林欄位（has_lease、caregiver、care_need、employment_insured）\
只在確定為真時輸出 true，絕不輸出 false。
- residence_city 只允許 Taipei（臺北市）或 Kaohsiung（高雄市）；其他縣市請省略。
- event_type 只允許 unemployment（失業）、illness（生病/住院）、fire（火災）、\
major_accident（重大事故）、death_in_family（家人過世）。
- income_status 只允許 low_income（低收入戶）、mid_low_income（中低收入戶）、\
near_threshold（邊緣戶）、general（一般）。
- age 為使用者本人年齡的整數；敘述中是別人的年齡就省略。
- 不評斷資格、不給建議，只抽取欄位。"""


def _clean(raw: Any) -> dict[str, Any]:
    """Whitelist wash: keep only known fields with valid canonical values."""
    if not isinstance(raw, dict):
        return {}
    profile: dict[str, Any] = {}
    for field, allowed in _ENUM_FIELDS.items():
        value = raw.get(field)
        if isinstance(value, str) and value in allowed:
            profile[field] = value
    for field in _BOOL_FIELDS:
        if raw.get(field) is True:
            profile[field] = True
    age = raw.get("age")
    if isinstance(age, bool):  # bool is an int subclass; never an age
        age = None
    if isinstance(age, int) and age in _AGE_RANGE:
        profile["age"] = age
    return profile


class OllamaIntentParser:
    """`IntentParser` adapter for a local Ollama chat endpoint."""

    def __init__(
        self,
        host: str | None = None,
        model: str | None = None,
        fallback: IntentParser | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self._host = (host or DEFAULT_HOST).rstrip("/")
        self._model = model or DEFAULT_MODEL
        self._fallback = fallback or DeterministicIntentParser()
        self._client = client or httpx.Client(timeout=TIMEOUT)

    def extract(self, text: str) -> dict[str, Any]:
        deterministic = self._fallback.extract(text)
        try:
            llm_profile = self._extract_llm(text)
        except (httpx.HTTPError, json.JSONDecodeError, KeyError, TypeError) as exc:
            logger.warning("ollama intent extraction failed, using fallback: %s", exc)
            return deterministic
        # Deterministic hits win: keyword matches are high precision, and the
        # 12 demo regression scenarios stay guaranteed with the LLM enabled.
        return {**llm_profile, **deterministic}

    def _extract_llm(self, text: str) -> dict[str, Any]:
        response = self._client.post(
            f"{self._host}/api/chat",
            json={
                "model": self._model,
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                "stream": False,
                "format": _FORMAT_SCHEMA,
                "options": {"temperature": 0},
            },
        )
        response.raise_for_status()
        content = response.json()["message"]["content"]
        return _clean(json.loads(content))


def build_intent_parser(settings: Settings) -> IntentParser:
    """Pick the parser from settings; deterministic unless explicitly opted in."""
    if settings.ollama_intent_enabled:
        return OllamaIntentParser(host=settings.ollama_host, model=settings.ollama_model)
    return DeterministicIntentParser()
