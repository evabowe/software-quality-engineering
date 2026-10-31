"""Tests für das Matching von Findings gegen die Ground Truth (Regeln aus Spec 8.6)."""

from judge_lab.matching import match_findings
from judge_lab.parsing import Finding
from judge_lab.snippets import get_snippet

BANK = get_snippet("bank_account").defects  # B1 26, B2 31, B3 39–40, Q1 24–25, Q2 33, Q3 42
SHUNTING = get_snippet("qb_shunting_yard").defects  # D1 17–18, Toleranz 15–18


def f(start, end=None, category="bug"):
    return Finding(line_start=start, line_end=end or start, category=category)


def test_adjacent_defects_bank():
    result = match_findings([f(25), f(26)], BANK)
    assert result.found_defect_ids == ("B1", "Q1")
    assert result.assignments == {0: "Q1", 1: "B1"}
    assert (result.tp, result.fp) == (2, 0)


def test_exact_hit_beats_tolerance_regardless_of_order():
    # Z. 26 trifft B1 exakt; Z. 25 liegt nur im Toleranzbereich von B1, aber exakt in Q1.
    result = match_findings([f(26), f(25)], BANK)
    assert result.assignments == {0: "B1", 1: "Q1"}


def test_single_finding_spanning_two_defects_hits_one():
    result = match_findings([f(24, 26)], BANK)
    assert result.tp == 1
    assert result.found_defect_ids == ("B1",)


def test_missing_line_shunting_yard():
    assert match_findings([f(16)], SHUNTING).found_defect_ids == ("D1",)
    after = match_findings([f(19)], SHUNTING)
    assert (after.tp, after.fp) == (0, 1)


def test_empty_findings():
    result = match_findings([], BANK)
    assert (result.tp, result.fp, result.neutral, result.n_defects) == (0, 0, 0, 6)
    assert result.recall == 0.0
    assert result.precision is None


def test_out_of_range_finding_is_fp():
    result = match_findings([f(500)], BANK)
    assert (result.tp, result.fp) == (0, 1)
    assert result.precision == 0.0


def test_category_irrelevant_for_hit():
    # Q2 ist ein Qualitätsdefekt, wird aber als bug gemeldet → zählt trotzdem.
    assert match_findings([f(33, category="bug")], BANK).found_defect_ids == ("Q2",)


def test_unmatched_robustness_is_fp():
    assert match_findings([f(10, category="robustness")], BANK).fp == 1


def test_unmatched_style_and_maintainability_are_neutral():
    result = match_findings([f(38, category="style"), f(12, category="maintainability")], SHUNTING)
    assert (result.tp, result.fp, result.neutral) == (0, 0, 2)


def test_duplicate_findings_count_once():
    result = match_findings([f(26), f(26), f(26, category="style")], BANK)
    assert (result.tp, result.fp, result.neutral) == (1, 1, 1)


def test_metrics():
    result = match_findings([f(26), f(31), f(10)], BANK)
    assert result.recall == 2 / 6
    assert result.precision == 2 / 3


def test_no_defects_gives_no_recall():
    result = match_findings([f(1)], [])
    assert result.recall is None
    assert result.fp == 1
