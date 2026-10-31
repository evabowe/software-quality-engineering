"""Tolerantes Parsen der Judge-Antworten.

LLMs halten das JSON-Format nicht immer ein: Sie schreiben Prosa davor,
setzen Markdown-Fences, liefern Zahlen als Text oder erfinden Kategorien.
Hier wird so viel wie möglich gerettet; nur wenn gar kein JSON-Objekt
erkennbar ist, entsteht ein ``ParseError`` (→ Reparatur-Retry im Runner).
"""

from __future__ import annotations

import json
import re
from typing import Literal

from pydantic import BaseModel

from judge_lab.config import WEIGHTS

Category = Literal["bug", "robustness", "maintainability", "style"]
Severity = Literal["high", "medium", "low"]

REPAIR_MESSAGE = (
    "Your previous answer could not be parsed. Respond again with only the JSON object "
    "described in the output format above: no Markdown fences, no text before or after it."
)

_CATEGORY_SYNONYMS = {
    "bug": "bug", "correctness": "bug", "functional_correctness": "bug", "functional": "bug",
    "logic": "bug", "error": "bug", "defect": "bug",
    "robustness": "robustness", "reliability": "robustness", "security": "robustness",
    "performance": "robustness", "edge_case": "robustness",
    "maintainability": "maintainability",
    "style": "style", "readability": "style", "naming": "style", "documentation": "style",
    "formatting": "style",
}
_THINK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")
# Für Zeilen ohne Vorzeichen, damit "12-14" als Bereich gelesen wird.
_LINE_NUMBER = re.compile(r"\d+")


class ParseError(ValueError):
    """Die Antwort enthält kein verwertbares JSON-Objekt."""


class Finding(BaseModel):
    line_start: int
    line_end: int
    category: Category
    severity: Severity = "medium"
    description: str = ""
    suggested_fix: str = ""


class JudgeVerdict(BaseModel):
    findings: list[Finding] = []
    scores: dict[str, float] = {}
    overall_score: float | None = None


def _balanced_object_end(text: str, start: int) -> int | None:
    """Index hinter der schließenden Klammer des Objekts ab ``start``; beachtet String-Literale."""
    depth, in_string, escaped = 0, False, False
    for i in range(start, len(text)):
        char = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return i + 1
    return None


def extract_json(text: str) -> dict:
    """Erstes vollständiges JSON-Objekt im Text (Prosa, Fences und <think>-Blöcke werden übergangen)."""
    text = _THINK.sub("", text or "")
    for start in (i for i, char in enumerate(text) if char == "{"):
        end = _balanced_object_end(text, start)
        if end is None:
            continue
        try:
            value = json.loads(text[start:end])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise ParseError("Kein JSON-Objekt in der Antwort gefunden.")


def _numbers(value, pattern: re.Pattern = _NUMBER) -> list[float]:
    if isinstance(value, bool) or value is None:
        return []
    if isinstance(value, (int, float)):
        return [float(value)]
    return [float(n) for n in pattern.findall(str(value))]


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _category(raw) -> Category:
    key = str(raw or "").strip().lower().replace(" ", "_").replace("-", "_")
    return _CATEGORY_SYNONYMS.get(key, "maintainability")


def _severity(raw) -> Severity:
    key = str(raw or "").strip().lower()
    return key if key in ("high", "medium", "low") else "medium"


def _finding(item: dict, line_count: int) -> Finding | None:
    start_numbers = _numbers(item.get("line_start"), _LINE_NUMBER)
    if not start_numbers:
        return None
    start = int(start_numbers[0])
    # "12-14" in line_start gilt als Bereich.
    end_numbers = _numbers(item.get("line_end"), _LINE_NUMBER) or start_numbers[1:2] or [start]
    end = int(end_numbers[0])
    start, end = sorted((start, end))
    upper = max(line_count, 1)
    return Finding(
        line_start=int(_clamp(start, 1, upper)),
        line_end=int(_clamp(end, 1, upper)),
        category=_category(item.get("category")),
        severity=_severity(item.get("severity")),
        description=str(item.get("description") or ""),
        suggested_fix=str(item.get("suggested_fix") or ""),
    )


def parse_verdict(text: str, line_count: int) -> JudgeVerdict:
    data = extract_json(text)
    raw_findings = data.get("findings") or []
    if not isinstance(raw_findings, list):
        raise ParseError("„findings“ ist keine Liste.")
    findings = [
        finding
        for item in raw_findings
        if isinstance(item, dict) and (finding := _finding(item, line_count)) is not None
    ]

    raw_scores = data.get("scores") if isinstance(data.get("scores"), dict) else {}
    scores = {}
    for key in WEIGHTS:
        numbers = _numbers(raw_scores.get(key))
        if numbers:
            scores[key] = _clamp(numbers[0], 0, 10)

    overall = _numbers(data.get("overall_score"))
    return JudgeVerdict(
        findings=findings,
        scores=scores,
        overall_score=_clamp(overall[0], 0, 10) if overall else None,
    )
