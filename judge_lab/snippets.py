"""Snippet-Registry: lädt Code, Tests und Ground Truth aus ``snippets/<id>/``.

Jedes Snippet besteht aus der Programmdatei (Originalname, siehe ``code_file``),
``tests.py`` und ``meta.yaml``. Die Ground Truth (``defects``) bleibt im Python-
Prozess; ``public_view`` liefert alles, was gefahrlos angezeigt werden darf.
"""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

import yaml

from judge_lab.config import SNIPPETS_DIR


@dataclass(frozen=True)
class Defect:
    id: str
    kind: Literal["bug", "quality"]
    lines: tuple[int, int]
    accept_lines: tuple[int, int]
    description: str
    # Wörtlicher Ersatzcode inkl. Einrückung; leer bedeutet „Zeilen löschen“.
    fix: str
    fix_op: Literal["replace", "insert_after"] = "replace"
    quixbugs_class: str | None = None


@dataclass(frozen=True)
class Snippet:
    id: str
    title: str
    level: str | None
    cognitive: int | None
    loc: int | None
    spec: Literal["docstring", "trailing_string"]
    code_file: str
    code: str
    tests: str
    timeout_s: int
    source: dict = field(compare=False)
    defects: tuple[Defect, ...] = field(repr=False)

    @property
    def line_count(self) -> int:
        return len(self.code.splitlines())

    def numbered_code(self) -> str:
        """Code mit rechtsbündigen Zeilennummern, passend zu den Zeilen der Ground Truth."""
        return "\n".join(
            f"{n:>3} | {line}".rstrip() for n, line in enumerate(self.code.splitlines(), start=1)
        )

    def public_view(self) -> dict:
        """Alle Felder außer der Ground Truth, z. B. für die Anzeige im Notebook."""
        view = asdict(self)
        del view["defects"]
        return view

    def function_names(self) -> set[str]:
        """Namen aller Funktionen, Methoden und Klassen im Code."""
        tree = ast.parse(self.code)
        return {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        }

    def patched_code(self) -> str:
        """Code mit allen Korrekturen aus der Ground Truth (für die Plausibilisierung)."""
        lines = self.code.splitlines()
        # Von unten nach oben anwenden, damit die Zeilennummern weiter oben gültig bleiben.
        for defect in sorted(self.defects, key=lambda d: d.lines[0], reverse=True):
            replacement = defect.fix.splitlines()
            start, end = defect.lines
            if defect.fix_op == "insert_after":
                lines[start:start] = replacement
            else:
                lines[start - 1 : end] = replacement
        return "\n".join(lines) + "\n"


def _load_one(folder: Path) -> Snippet:
    meta = yaml.safe_load((folder / "meta.yaml").read_text(encoding="utf-8"))
    complexity = meta.get("complexity") or {}
    defects = tuple(
        Defect(
            id=d["id"],
            kind=d["kind"],
            lines=tuple(d["lines"]),
            accept_lines=tuple(d["accept_lines"]),
            description=d["description"],
            fix=d.get("fix", ""),
            fix_op=d.get("fix_op", "replace"),
            quixbugs_class=d.get("quixbugs_class"),
        )
        for d in meta.get("defects") or []
    )
    return Snippet(
        id=meta["id"],
        title=meta["title"],
        level=complexity.get("level"),
        cognitive=complexity.get("cognitive"),
        loc=complexity.get("loc"),
        spec=meta["spec"],
        code_file=meta["code_file"],
        code=(folder / meta["code_file"]).read_text(encoding="utf-8"),
        tests=(folder / "tests.py").read_text(encoding="utf-8"),
        timeout_s=meta["tests"]["timeout_s"],
        source=meta.get("source") or {},
        defects=defects,
    )


def load_snippets(root: Path = SNIPPETS_DIR) -> list[Snippet]:
    """Alle Snippets, sortiert nach Komplexitätsstufe L1–L5; Snippets ohne Stufe zuletzt."""
    snippets = [_load_one(meta.parent) for meta in root.glob("*/meta.yaml")]
    return sorted(snippets, key=lambda s: (s.level is None, s.level or "", s.id))


def get_snippet(snippet_id: str, root: Path = SNIPPETS_DIR) -> Snippet:
    for snippet in load_snippets(root):
        if snippet.id == snippet_id:
            return snippet
    raise KeyError(f"Unbekanntes Snippet: {snippet_id!r}")
