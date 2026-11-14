"""LLM-Clients: ein OpenAI-kompatibler Client für OpenRouter sowie ein Mock.

Retries mit exponentiellem Backoff bei 429/5xx/Timeout übernimmt das openai-SDK.
"""

from __future__ import annotations

import json
import time
from collections.abc import Sequence
from dataclasses import dataclass

from openai import OpenAI

from judge_lab.config import MAX_RETRIES, MAX_TOKENS, OPENROUTER_BASE_URL, TEMPERATURE, TIMEOUT_S
from judge_lab.snippets import Snippet, load_snippets


class ConfigError(ValueError):
    """Fehlende oder unvollständige Konfiguration (API-Key, Code)."""


@dataclass(frozen=True)
class LLMResult:
    text: str
    latency_s: float
    tokens_in: int | None
    tokens_out: int | None
    error: str | None = None
    finish_reason: str | None = None  # "length" = an max_tokens abgeschnitten


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
            finish_reason=response.choices[0].finish_reason,
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


def make_client(modell: str, api_key: str | None) -> ChatClient | MockClient:
    """Client für eine OpenRouter-Modell-ID; ``"mock"`` liefert den Mock-Client ohne Key."""
    if modell == "mock":
        return MockClient()
    if not api_key:
        raise ConfigError(
            'Es fehlt der OpenRouter-Key. Bitte zuerst verbinde("CODE") mit dem Code von der Folie ausführen.'
        )
    return ChatClient(OPENROUTER_BASE_URL, api_key, modell, provider="openrouter", timeout_s=TIMEOUT_S)
