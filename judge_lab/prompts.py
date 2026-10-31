"""Komposition der Judge-Prompts aus den Bausteinen in ``prompts/``.

Reihenfolge (siehe prompts/ADAPTATION.md):
[1] Haltungsblock bzw. Text der Gruppe + [2] Bewertungsskala → System-Message
[3] Aufgabe mit Code (+ Tests) + [4] Ausgabevertrag          → User-Message

Die Ground Truth eines Snippets wird hier bewusst nie verwendet.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence

from judge_lab.config import ATTITUDES, PROMPTS_DIR
from judge_lab.snippets import Snippet

SPEC_HINTS = {
    "docstring": "The specification is the module docstring at the top of the file.",
    "trailing_string": "The specification is the string block at the end of the file.",
}

_LINE_REFERENCE = re.compile(r"\b(?:lines?|zeilen?)\s*\d+|\bZ\.\s*\d+", re.IGNORECASE)


def _read(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8").strip()


def load_attitude(attitude: str) -> str:
    if attitude not in ATTITUDES:
        raise ValueError(f"Unbekannte Haltung {attitude!r}, erlaubt sind {ATTITUDES}")
    return _read(f"attitudes/{attitude}.md")


def _fill(template: str, values: dict[str, str]) -> str:
    # Bewusst kein str.format: Code und Tests enthalten geschweifte Klammern.
    for key, value in values.items():
        template = template.replace("{" + key + "}", value)
    return template


def build_prompt(
    snippet: Snippet,
    *,
    with_tests: bool,
    attitude: str | None = None,
    custom_block: str | None = None,
) -> list[dict[str, str]]:
    """Baut die Messages für einen Judge-Lauf; genau eines von ``attitude``/``custom_block``."""
    if (attitude is None) == (custom_block is None):
        raise ValueError("Genau eines von attitude und custom_block muss gesetzt sein.")
    block = load_attitude(attitude) if attitude is not None else custom_block.strip()

    tests_block = _fill(_read("tests_block.md"), {"tests": snippet.tests.rstrip()}) if with_tests else ""
    task = _fill(
        _read("task_template.md"),
        {
            "spec_hint": SPEC_HINTS[snippet.spec],
            "code_numbered": snippet.numbered_code(),
            "tests_block": "\n" + tests_block + "\n" if tests_block else "",
        },
    )
    return [
        {"role": "system", "content": f"{block}\n\n{_read('scale_iso25010.md')}"},
        {"role": "user", "content": f"{task}\n\n{_read('output_contract.md')}"},
    ]


def prompt_hash(block: str) -> str:
    """Kurzer, stabiler Fingerabdruck eines Haltungs- bzw. Challenge-Blocks fürs Scoreboard."""
    return hashlib.sha256(block.strip().encode("utf-8")).hexdigest()[:12]


def lint_challenge_prompt(text: str, snippets: Sequence[Snippet]) -> list[str]:
    """Warnt vor snippetspezifischen Hinweisen im Challenge-Prompt (blockiert nicht)."""
    warnings = []
    if _LINE_REFERENCE.search(text):
        warnings.append(
            "Euer Prompt nennt Zeilennummern. Er muss für alle Snippets funktionieren – "
            "bitte keine Hinweise auf bestimmte Stellen."
        )
    names = {name for s in snippets for name in s.function_names() if not name.startswith("__")}
    found = sorted(name for name in names if re.search(rf"\b{re.escape(name)}\b", text))
    if found:
        warnings.append(
            f"Euer Prompt nennt Funktions- oder Klassennamen aus den Snippets ({', '.join(found)}). "
            "Bitte allgemein formulieren."
        )
    return warnings
