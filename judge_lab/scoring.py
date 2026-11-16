"""Gewichteter Gesamtscore und Punkte der Prompt-Challenge."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from judge_lab.config import POINTS, WEIGHTS
from judge_lab.matching import MatchResult


def weighted_score(scores: Mapping[str, float]) -> float | None:
    """Gesamtscore nach WEIGHTS; None, wenn eine Dimension fehlt (dann ist kein fairer Vergleich möglich)."""
    if any(key not in scores for key in WEIGHTS):
        return None
    return round(sum(scores[key] * weight for key, weight in WEIGHTS.items()), 2)


def challenge_points(results: Iterable[MatchResult]) -> int:
    """Σ (2·Treffer − 1·False Positive − 3·übersehener Defekt) über alle Snippets einer Einreichung."""
    return sum(POINTS["tp"] * r.tp + POINTS["fp_bug"] * r.fp + POINTS["fn"] * (r.n_defects - r.tp) for r in results)
