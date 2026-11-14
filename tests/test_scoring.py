"""Tests für Konfiguration, gewichteten Score und Challenge-Punkte."""

import math

from judge_lab import config
from judge_lab.matching import MatchResult
from judge_lab.scoring import challenge_points, weighted_score


def _result(tp, fp):
    return MatchResult(tp=tp, fp=fp, neutral=0, n_defects=1, found_defect_ids=(), assignments={},
                       recall=None, precision=None)


def test_weighted_score():
    # 0.40*10 + 0.20*5 + 0.25*6 + 0.15*8 = 7.7
    scores = {"functional_correctness": 10, "reliability": 5, "maintainability": 6, "readability": 8}
    assert weighted_score(scores) == 7.7


def test_weighted_score_missing_dimension():
    assert weighted_score({"functional_correctness": 10, "reliability": 5, "maintainability": 6}) is None


def test_challenge_points():
    # 2 Punkte je Treffer, -1 je False Positive, über alle Snippets summiert
    assert challenge_points([_result(2, 1), _result(1, 1), _result(0, 0)]) == 4


def test_weights_sum_to_one():
    assert math.isclose(sum(config.WEIGHTS.values()), 1.0)
