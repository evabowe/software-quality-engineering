"""Schritt 1: Die Gruppe begutachtet ``bank_account`` selbst, in ihrer verdeckten Rolle.

Ihre Angaben werden mit derselben Logik gemessen wie die LLM-Judges (``matching.py``)
und als Datensatz mit ``phase="human"`` gesendet. Die Rückmeldung nennt nur Anzahlen,
nie die Zeilen der Defekte.
"""

from __future__ import annotations

import json
import re

from judge_lab.config import FINDINGS_JSON_MAX, HUMAN_ROLES, HUMAN_SNIPPET, PROMPTS_DIR
from judge_lab.matching import match_findings
from judge_lab.parsing import Finding
from judge_lab.runner import RunContext, _empty_record
from judge_lab.snippets import get_snippet

FORMAT_HINT = "Format: 26, 31, 39-40"
NONE_WORDS = {"keine", "-"}
_TOKEN = re.compile(r"^(\d+)(?:-(\d+))?$")


class InputError(ValueError):
    """Eingabe der Gruppe ist nicht lesbar; die Meldung ist deutsch und zeigbar."""


def parse_lines(text: str, line_count: int) -> list[Finding]:
    """„26, 31, 39-40“ → ein Finding (Kategorie bug) je Zeile bzw. Bereich; „keine“ → leere Liste."""
    text = (text or "").strip()
    if text.lower() in NONE_WORDS:
        return []
    if not text:
        raise InputError(f"Bitte mindestens eine Zeile angeben – oder „keine“ eintragen. {FORMAT_HINT}")
    # Gedankenstriche vereinheitlichen, Leerzeichen um Bindestriche entfernen
    text = re.sub(r"\s*[-–—]\s*", "-", text)
    spans = set()
    for token in re.split(r"[,;\s]+", text):
        match = _TOKEN.match(token)
        if not match:
            raise InputError(f"„{token}“ ist keine Zeilennummer. {FORMAT_HINT}")
        start = int(match.group(1))
        end = int(match.group(2) or start)
        if start > end:
            raise InputError(f"Im Bereich {token} steht der Anfang hinter dem Ende. Gemeint ist wohl {end}-{start}.")
        for line in (start, end):
            if not 1 <= line <= line_count:
                raise InputError(f"Zeile {line} gibt es nicht – der Code hat {line_count} Zeilen.")
        spans.add((start, end))
    return [Finding(line_start=s, line_end=e, category="bug") for s, e in sorted(spans)]


def load_role_cards() -> dict[str, str]:
    """Haltung (bzw. „none“) → Text der Rollenkarte."""
    text = (PROMPTS_DIR / "role_cards_de.md").read_text(encoding="utf-8")
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    cards = {}
    for section in re.split(r"^## ", text, flags=re.MULTILINE)[1:]:
        name, _, body = section.partition("\n")
        cards[name.strip()] = body.strip()
    return cards


def role_of(group: str) -> str:
    return HUMAN_ROLES.get(group) or "none"


def role_card(group: str) -> str:
    return load_role_cards()[role_of(group)]


def human_record(ctx: RunContext, findings: list[Finding], *, score: int, justification: str) -> dict:
    """Datensatz des Gutachtens; wird sofort gesendet."""
    snippet = get_snippet(HUMAN_SNIPPET)
    match = match_findings(findings, snippet.defects)
    record = _empty_record(ctx, "human")
    stored = {"justification": justification, "findings": [f.model_dump() for f in findings]}
    record.update(
        model_key="human",
        model_id="human",
        attitude=role_of(ctx.group),
        snippet_id=snippet.id,
        complexity_level=snippet.level or "",
        with_tests=False,
        tp=match.tp,
        fp=match.fp,
        neutral=match.neutral,
        n_defects=match.n_defects,
        recall=match.recall,
        precision=match.precision,
        weighted_score=score,
        found_defect_ids=",".join(match.found_defect_ids),
        findings_json=json.dumps(stored, ensure_ascii=False)[:FINDINGS_JSON_MAX],
        parse_ok=True,
    )
    ctx.sink(record)
    return record


def justification_of(record: dict) -> str:
    try:
        return json.loads(record["findings_json"]).get("justification", "")
    except (json.JSONDecodeError, AttributeError):
        return ""


def feedback(record: dict) -> str:
    """Nur Anzahlen – welche Defekte gefunden wurden, bleibt bis zur Auflösung offen."""
    fp = record["fp"]
    false_alarms = "1 Meldung war kein Defekt" if fp == 1 else f"{fp} Meldungen waren keine Defekte"
    return f"Ihr habt {record['tp']} von {record['n_defects']} Defekten gefunden, {false_alarms}."
