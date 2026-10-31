"""Matching der Judge-Findings gegen die Ground Truth (Regeln aus dem Konzept, Abschnitt 8.6).

1. Ein Finding trifft Defekt D, wenn sich seine Zeilen mit ``D.accept_lines`` überschneiden.
2. Exakte Überschneidung mit ``D.lines`` geht vor dem Toleranzbereich, danach zählt der
   kleinste Abstand. Jedes Finding trifft höchstens einen Defekt, jeder Defekt zählt höchstens
   einmal (greedy, deterministisch sortiert).
3. Ein Treffer zählt unabhängig von der Kategorie.
4. Nicht zugeordnete Findings der Kategorie bug/robustness sind False Positives,
5. nicht zugeordnete maintainability/style-Findings sind neutral.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from judge_lab.parsing import Finding
from judge_lab.snippets import Defect

FP_CATEGORIES = {"bug", "robustness"}


@dataclass(frozen=True)
class MatchResult:
    tp: int
    fp: int
    neutral: int
    n_defects: int
    found_defect_ids: tuple[str, ...]
    assignments: dict[int, str]  # Index des Findings → Defekt-ID
    recall: float | None
    precision: float | None


def _overlaps(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return a[0] <= b[1] and b[0] <= a[1]


def _gap(a: tuple[int, int], b: tuple[int, int]) -> int:
    """Anzahl Zeilen zwischen zwei Bereichen; 0 bei Überschneidung."""
    return max(0, b[0] - a[1], a[0] - b[1])


def match_findings(findings: Sequence[Finding], defects: Sequence[Defect]) -> MatchResult:
    candidates = []
    for index, finding in enumerate(findings):
        span = (finding.line_start, finding.line_end)
        for defect in defects:
            if _overlaps(span, defect.accept_lines):
                exact = 0 if _overlaps(span, defect.lines) else 1
                candidates.append((exact, _gap(span, defect.lines), index, defect.id))

    assignments: dict[int, str] = {}
    for _, _, index, defect_id in sorted(candidates):
        if index not in assignments and defect_id not in assignments.values():
            assignments[index] = defect_id

    unmatched = [f for i, f in enumerate(findings) if i not in assignments]
    tp = len(assignments)
    fp = sum(1 for f in unmatched if f.category in FP_CATEGORIES)
    return MatchResult(
        tp=tp,
        fp=fp,
        neutral=len(unmatched) - fp,
        n_defects=len(defects),
        found_defect_ids=tuple(sorted(assignments.values())),
        assignments=dict(sorted(assignments.items())),
        recall=tp / len(defects) if defects else None,
        precision=tp / (tp + fp) if tp + fp else None,
    )
