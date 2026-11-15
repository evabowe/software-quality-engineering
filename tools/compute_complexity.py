"""Misst die kognitive Komplexität aller Snippets mit complexipy und trägt sie in meta.yaml ein.

Aufruf (von der Projektwurzel):

    python tools/compute_complexity.py

Geschrieben werden nur ``complexity.cognitive`` (Summe über alle Funktionen,
wie im Komplexitäts-Notebook) und ``complexity.loc`` (nicht-leere Zeilen der
Programmdatei). Alle anderen Zeilen und Kommentare der meta.yaml bleiben erhalten.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml
from complexipy import file_complexity

REPO_ROOT = Path(__file__).resolve().parent.parent


def measure(snippet_dir: Path) -> dict:
    meta = yaml.safe_load((snippet_dir / "meta.yaml").read_text(encoding="utf-8"))
    code_path = snippet_dir / meta["code_file"]
    functions = file_complexity(str(code_path)).functions
    loc = sum(1 for line in code_path.read_text(encoding="utf-8").splitlines() if line.strip())
    return {"cognitive": sum(f.complexity for f in functions), "loc": loc}


def update_meta(meta_path: Path, values: dict) -> None:
    text = meta_path.read_text(encoding="utf-8")
    for key, value in values.items():
        # Ersetzt die eingerückte Zeile im complexity-Block samt Kommentar.
        text = re.sub(rf"^(  {key}:).*$", rf"\g<1> {value}", text, count=1, flags=re.MULTILINE)
    meta_path.write_text(text, encoding="utf-8")


def main() -> int:
    for meta_path in sorted((REPO_ROOT / "snippets").rglob("meta.yaml")):
        values = measure(meta_path.parent)
        update_meta(meta_path, values)
        print(f"{meta_path.parent.name:<22} kognitiv {values['cognitive']:>3}   LOC {values['loc']:>3}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
