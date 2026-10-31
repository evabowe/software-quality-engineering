"""LLM-Clients: ein OpenAI-kompatibler Client für OpenRouter und Ollama sowie ein Mock.

OpenRouter und Ollama sprechen beide das Chat-Completions-Format; nur
``base_url``, ``api_key`` und Modell-ID unterscheiden sich. Retries mit
exponentiellem Backoff bei 429/5xx/Timeout übernimmt das openai-SDK.
"""

from __future__ import annotations

import json
import time
from collections.abc import Sequence
from dataclasses import dataclass

from openai import OpenAI

from judge_lab.config import (
    MAX_RETRIES,
    MAX_TOKENS,
    MODELS,
    OLLAMA_BASE_URL,
    OPENROUTER_BASE_URL,
    PLACEHOLDER_MARK,
    TEMPERATURE,
    TIMEOUTS,
)
from judge_lab.snippets import Snippet, load_snippets


class ConfigError(ValueError):
    """Fehlende oder unvollständige Konfiguration (API-Key, Modell-ID)."""


@dataclass(frozen=True)
class LLMResult:
    text: str
    latency_s: float
    tokens_in: int | None
    tokens_out: int | None
    error: str | None = None


class ChatClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        *,
        provider: str,
        timeout_s: float,
        max_retries: int = MAX_RETRIES,
    ):
        self.provider = provider
        self.model_id = model
        self._client = OpenAI(base_url=base_url, api_key=api_key, timeout=timeout_s, max_retries=max_retries)

    def complete(self, messages: list[dict]) -> LLMResult:
        """Ein Chat-Aufruf. Wirft nie: Fehler stehen in ``LLMResult.error``."""
        started = time.perf_counter()
        try:
            response = self._client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                response_format={"type": "json_object"},
            )
        except Exception as exc:  # noqa: BLE001 – jeder Fehler soll den Lauf markieren, nicht abbrechen
            return LLMResult("", time.perf_counter() - started, None, None, f"LLM-Aufruf fehlgeschlagen: {exc}")
        usage = response.usage
        return LLMResult(
            text=response.choices[0].message.content or "",
            latency_s=time.perf_counter() - started,
            tokens_in=usage.prompt_tokens if usage else None,
            tokens_out=usage.completion_tokens if usage else None,
        )


# --- Mock -------------------------------------------------------------------

_MOCK_SCORES = {"Chief Embedded Software Architect": 3, "Senior System Engineer": 5, "Technical Product Manager": 7}
_MOCK_BROKEN = {"qb_levenshtein"}  # liefert immer kaputtes JSON → parse_ok=False
_MOCK_PROSE = {"qb_shunting_yard"}  # JSON in Prosa und Markdown-Fence → Extraktion


class MockClient:
    """Deterministischer Provider für Tests, Proben und als Notfall-Fallback (keine Kosten).

    Erkennt das Snippet am nummerierten Code im Prompt und liefert pro Snippet einen
    Treffer, einen False Positive und ein neutrales Style-Finding. Die Beschreibungen
    sind generisch und verraten nichts aus der Ground Truth.
    """

    provider = "mock"
    model_id = "mock"

    def __init__(self, snippets: Sequence[Snippet] | None = None):
        self._snippets = list(snippets) if snippets is not None else load_snippets()

    def complete(self, messages: list[dict]) -> LLMResult:
        system = messages[0]["content"]
        task = next(m["content"] for m in messages if m["role"] == "user")
        snippet = next((s for s in self._snippets if s.numbered_code() in task), None)
        if snippet is None:
            return LLMResult("{}", 0.0, 0, 0)
        if snippet.id in _MOCK_BROKEN:
            return LLMResult('{"findings": [{"line_start": 3, "description": "Mock-Befund"', 0.0, len(task) // 4, 12)

        score = next((v for role, v in _MOCK_SCORES.items() if role in system), 6)
        accepted = {n for d in snippet.defects for n in range(d.accept_lines[0], d.accept_lines[1] + 1)}
        free_line = next(n for n in range(1, snippet.line_count + 1) if n not in accepted)
        hit = snippet.defects[0].lines[0]
        answer = {
            "findings": [
                {"line_start": hit, "line_end": hit, "category": "bug", "severity": "high",
                 "description": "Mock-Befund: Diese Zeile wirkt fehlerhaft.", "suggested_fix": ""},
                {"line_start": free_line, "line_end": free_line, "category": "bug", "severity": "medium",
                 "description": "Mock-Befund: möglicher Fehler (Fehlalarm).", "suggested_fix": ""},
                {"line_start": free_line, "line_end": free_line, "category": "style", "severity": "low",
                 "description": "Mock-Befund: Benennung könnte klarer sein.", "suggested_fix": ""},
            ],
            "scores": {"functional_correctness": score, "reliability": score,
                       "maintainability": score, "readability": score},
            "overall_score": score,
        }
        text = json.dumps(answer)
        if snippet.id in _MOCK_PROSE:
            text = f"Here is my review:\n```json\n{text}\n```\nLet me know if you need more details."
        return LLMResult(text, 0.0, len(task) // 4, len(text) // 4)


# --- Fabrik -----------------------------------------------------------------


def make_client(model_key: str, api_key: str | None) -> ChatClient | MockClient:
    """Client für einen Eintrag aus ``config.MODELS``; prüft Key und Modell-ID vorab."""
    if model_key not in MODELS:
        raise ConfigError(f"Unbekanntes Modell {model_key!r}. Bekannt sind: {', '.join(MODELS)}.")
    model = MODELS[model_key]
    if model["provider"] == "mock":
        return MockClient()
    if PLACEHOLDER_MARK in model["id"]:
        raise ConfigError(
            f"Die Modell-ID für {model['label']} ist noch ein Platzhalter ({model['id']}). "
            "Bitte in judge_lab/config.py eintragen."
        )
    if model["provider"] == "ollama":
        return ChatClient(OLLAMA_BASE_URL, "ollama", model["id"], provider="ollama", timeout_s=TIMEOUTS["ollama"])
    if not api_key:
        raise ConfigError("Es fehlt der OpenRouter-API-Key. Bitte im Setup eintragen (siehe Folie).")
    return ChatClient(OPENROUTER_BASE_URL, api_key, model["id"], provider="openrouter", timeout_s=TIMEOUTS["openrouter"])
