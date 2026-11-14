"""Komposition der Judge-Prompts aus den Bausteinen in ``prompts/``.

[1] Prompt der Gruppe + [2] Bewertungsskala (ISO/IEC 25010) → System-Message
[3] Aufgabe mit nummeriertem Code + [4] Antwortformat (JSON) → User-Message

Die Ground Truth eines Snippets wird hier bewusst nie verwendet.
"""

from __future__ import annotations

from judge_lab.config import PROMPTS_DIR
from judge_lab.snippets import Snippet

SPEC_HINTS = {
    "docstring": "The specification is the module docstring at the top of the file.",
    "trailing_string": "The specification is the string block at the end of the file.",
}


def _read(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8").strip()


def _fill(template: str, values: dict[str, str]) -> str:
    # Bewusst kein str.format: Code enthält geschweifte Klammern.
    for key, value in values.items():
        template = template.replace("{" + key + "}", value)
    return template


def build_prompt(snippet: Snippet, prompt: str) -> list[dict[str, str]]:
    """Messages für einen Judge-Aufruf: Prompt der Gruppe + Skala als System-, Code + Antwortformat als User-Message."""
    task = _fill(
        _read("task_template.md"),
        {"spec_hint": SPEC_HINTS[snippet.spec], "code_numbered": snippet.numbered_code()},
    )
    return [
        {"role": "system", "content": f"{prompt.strip()}\n\n{_read('scale_iso25010.md')}"},
        {"role": "user", "content": f"{task}\n\n{_read('output_contract.md')}"},
    ]
