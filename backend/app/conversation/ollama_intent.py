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
# Measured on the demo scenarios (2026-07-02): qwen2.5:1.5b beat qwen3:4b
# (non-thinking) on zh-TW extraction with zero hallucinated fields, and is
# smaller/faster. Override with OLLAMA_MODEL.
DEFAULT_MODEL = "qwen2.5:1.5b"
# Local single-turn extraction; fail fast so the fallback keeps the chat snappy.
TIMEOUT = httpx.Timeout(10.0, connect=2.0)

# Canonical profile tokens (docs/data.md). Anything outside these is dropped.
# income_status is deliberately NOT extractable by the LLM: it is a
# government-certified status the model keeps inferring from mere hardship
# ("經濟出狀況" -> low_income), and a false positive skews eligibility. The
# formal wordings (低收/中低收/邊緣戶) are covered by the keyword parser, and
# otherwise the rule engine asks the follow-up question.
_ENUM_FIELDS: dict[str, frozenset[str]] = {
    "residence_city": frozenset({"Taipei", "Kaohsiung"}),
    "event_type": frozenset(
        {"unemployment", "illness", "fire", "major_accident", "death_in_family"}
    ),
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
- 不要輸出收入身分；經濟困難與否由系統另外詢問。
- age 為使用者本人年齡的整數（中文數字也要轉換，如「四十二歲」→ 42）；是別人的年齡就省略。
- 口語、台語也要理解（「頭路無去/無頭路」= unemployment、「阿嬤走了/過世」= \
death_in_family、「租厝」= has_lease、「四十二歲」= age 42）。
- 不評斷資格、不給建議，只抽取欄位。"""


# Small local models copy fields out of instructions or thin air. Each of
# these LLM-extracted fields must be backed by at least one marker actually
# present in the user's text, or it is dropped (untrusted-input principle).
_EVIDENCE_MARKERS: dict[str, tuple[str, ...]] = {
    "age": ("歲", "今年", "年紀", "年齡"),
    "has_lease": ("租", "厝"),
    "caregiver": ("照", "顧", "護"),
    "care_need": ("失能", "失智", "臥床", "長照", "照", "顧", "護", "重度"),
    "employment_insured": ("勞保", "就業保險", "保"),
}


def _evidence_gate(text: str, profile: dict[str, Any]) -> dict[str, Any]:
    gated = dict(profile)
    for field, markers in _EVIDENCE_MARKERS.items():
        if field not in gated:
            continue
        has_digits = field == "age" and any(ch.isdigit() for ch in text)
        if not has_digits and not any(marker in text for marker in markers):
            del gated[field]
    return gated


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
                # Thinking models (qwen3) burn the whole timeout on reasoning
                # tokens before the JSON; non-thinking models accept false too.
                "think": False,
                "format": _FORMAT_SCHEMA,
                "options": {"temperature": 0},
            },
        )
        response.raise_for_status()
        content = response.json()["message"]["content"]
        return _evidence_gate(text, _clean(json.loads(content)))


def build_intent_parser(settings: Settings) -> IntentParser:
    """Pick the parser from settings; deterministic unless explicitly opted in."""
    if settings.ollama_intent_enabled:
        return OllamaIntentParser(host=settings.ollama_host, model=settings.ollama_model)
    return DeterministicIntentParser()
