"""Übernimmt Programme aus einem QuixBugs-Checkout als Snippets.

Aufruf (von der Projektwurzel):

    python tools/import_quixbugs.py <pfad-zum-quixbugs-checkout> bitcount quicksort …

Pro Programm entsteht ``snippets/qb_<name>/`` mit
- ``<name>.py``: byte-identische Kopie aus ``python_programs/``,
- ``tests.py``: die ersten 6 Fälle aus ``json_testcases/<name>.json`` als lesbare pytest-Funktionen,
- ``meta.yaml``: Herkunft (Commit, SHA-256). Die Ground Truth (``defects``) wird
  manuell gepflegt; eine vorhandene ``meta.yaml`` wird nur in ``commit`` und
  ``sha256`` aktualisiert, damit Kommentare und Defekte erhalten bleiben.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
QUIXBUGS_URL = "https://github.com/jkoppel/QuixBugs"
MAX_CASES = 6


def render_tests(name: str, cases: list) -> str:
    """Erzeugt tests.py aus JSON-Testfällen der Form ``[argumente, erwartet]``."""
    parts = [
        f'"""Tests für {name}.',
        "",
        "Automatisch erzeugt von tools/import_quixbugs.py aus QuixBugs",
        f"json_testcases/{name}.json (die ersten {MAX_CASES} Testfälle).",
        '"""',
        "",
        f"from {name} import {name}",
    ]
    for number, (args, expected) in enumerate(cases[:MAX_CASES], start=1):
        call = ", ".join(repr(arg) for arg in args)
        parts += ["", "", f"def test_case_{number}():", f"    assert {name}({call}) == {expected!r}"]
    return "\n".join(parts) + "\n"


def _read_cases(path: Path) -> list:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _title(code: str, fallback: str) -> str:
    """Erste nicht-leere Zeile des Spezifikations-Strings am Dateiende."""
    module = ast.parse(code)
    for node in reversed(module.body):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            for line in node.value.value.splitlines():
                if line.strip():
                    return line.strip()
    return fallback


def _git_commit(checkout: Path) -> str:
    result = subprocess.run(["git", "-C", str(checkout), "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def _skeleton(name: str, title: str, commit: str, sha256: str) -> str:
    return f"""# Ground Truth für ein QuixBugs-Programm. Wird nie an ein LLM gesendet.
id: qb_{name}
title: {title}
code_file: {name}.py
source:
  name: QuixBugs
  url: {QUIXBUGS_URL}
  file: python_programs/{name}.py
  commit: {commit}
  sha256: {sha256}
  license: MIT
complexity:
  level: null               # manuell setzen (L1–L5)
  cognitive: null           # wird von tools/compute_complexity.py gesetzt
  loc: null
spec: trailing_string       # Spezifikation steht als String am Dateiende
tests:
  origin: generated_from_json_testcases
  timeout_s: 5
defects:
"""


def _update_source(meta: str, commit: str, sha256: str) -> str:
    meta = re.sub(r"^(\s+commit:).*$", rf"\g<1> {commit}", meta, count=1, flags=re.MULTILINE)
    return re.sub(r"^(\s+sha256:).*$", rf"\g<1> {sha256}", meta, count=1, flags=re.MULTILINE)


def import_program(checkout: Path, name: str, dest_root: Path, commit: str | None = None) -> Path:
    """Übernimmt ein Programm und gibt den Snippet-Ordner zurück."""
    commit = commit or _git_commit(checkout)
    code = (checkout / "python_programs" / f"{name}.py").read_bytes()
    sha256 = hashlib.sha256(code).hexdigest()

    folder = dest_root / f"qb_{name}"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{name}.py").write_bytes(code)
    cases = _read_cases(checkout / "json_testcases" / f"{name}.json")
    (folder / "tests.py").write_text(render_tests(name, cases), encoding="utf-8")

    meta_path = folder / "meta.yaml"
    if meta_path.exists():
        meta_path.write_text(_update_source(meta_path.read_text(encoding="utf-8"), commit, sha256), encoding="utf-8")
    else:
        title = _title(code.decode("utf-8"), fallback=name)
        meta_path.write_text(_skeleton(name, title, commit, sha256), encoding="utf-8")
    return folder


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="QuixBugs-Programme als Snippets übernehmen")
    parser.add_argument("checkout", type=Path, help="Pfad zu einem QuixBugs-Checkout")
    parser.add_argument("names", nargs="+", help="Programmnamen, z. B. quicksort")
    args = parser.parse_args(argv)
    for name in args.names:
        folder = import_program(args.checkout, name, REPO_ROOT / "snippets")
        print(f"übernommen: {folder.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
