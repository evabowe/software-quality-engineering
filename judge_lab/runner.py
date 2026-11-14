"""Ein Judge-Aufruf mit genau einem Reparatur-Versuch bei unlesbarer Antwort."""

from __future__ import annotations

from judge_lab.llm import LLMResult
from judge_lab.parsing import REPAIR_MESSAGE, JudgeVerdict, ParseError, parse_verdict


def _combine(first: LLMResult, second: LLMResult) -> LLMResult:
    def total(a, b):
        return None if a is None and b is None else (a or 0) + (b or 0)

    return LLMResult(
        text=second.text,
        latency_s=first.latency_s + second.latency_s,
        tokens_in=total(first.tokens_in, second.tokens_in),
        tokens_out=total(first.tokens_out, second.tokens_out),
        error=second.error,
        finish_reason=second.finish_reason,
    )


def judge(client, messages: list[dict], line_count: int) -> tuple[JudgeVerdict | None, LLMResult, bool]:
    """Fragt den Judge; bei unlesbarer Antwort genau ein Reparatur-Versuch.

    Rückgabe: (Urteil oder None, zusammengefasstes LLM-Ergebnis, ob repariert wurde)
    """
    result = client.complete(messages)
    if result.error:
        return None, result, False
    try:
        return parse_verdict(result.text, line_count), result, False
    except ParseError:
        pass
    repair = messages + [
        {"role": "assistant", "content": result.text},
        {"role": "user", "content": REPAIR_MESSAGE},
    ]
    combined = _combine(result, client.complete(repair))
    if combined.error:
        return None, combined, True
    try:
        return parse_verdict(combined.text, line_count), combined, True
    except ParseError:
        return None, combined, True
