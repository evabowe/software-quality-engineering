"""Testhilfe: führt die Tests eines Snippets gegen beliebigen Code in einem Subprozess aus.

Ein Subprozess ist nötig, weil manche Defekte (z. B. ``bitcount``) eine
Endlosschleife erzeugen; der Timeout beendet sie zuverlässig.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from judge_lab.snippets import Snippet

# Großzügig gegenüber timeout_s, weil der Start von pytest selbst Zeit kostet.
TIMEOUT_FACTOR = 6


@dataclass(frozen=True)
class SnippetTestOutcome:
    passed: int
    failed: int
    timed_out: bool


def _count(summary: str, word: str) -> int:
    match = re.search(rf"(\d+) {word}", summary)
    return int(match.group(1)) if match else 0


def run_snippet_tests(snippet: Snippet, code: str, workdir: Path) -> SnippetTestOutcome:
    (workdir / snippet.code_file).write_text(code, encoding="utf-8")
    (workdir / "tests.py").write_text(snippet.tests, encoding="utf-8")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests.py", "-q", "-p", "no:cacheprovider"],
            cwd=workdir,
            env={**os.environ, "PYTHONPATH": str(workdir)},
            capture_output=True,
            text=True,
            timeout=snippet.timeout_s * TIMEOUT_FACTOR,
        )
    except subprocess.TimeoutExpired:
        return SnippetTestOutcome(passed=0, failed=0, timed_out=True)
    summary = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""
    return SnippetTestOutcome(
        passed=_count(summary, "passed"),
        failed=_count(summary, "failed") + _count(summary, "error"),
        timed_out=False,
    )
