"""Tests für levenshtein.

Automatisch erzeugt von tools/import_quixbugs.py aus QuixBugs
json_testcases/levenshtein.json (die ersten 6 Testfälle, die QuixBugs nicht überspringt).
"""

from levenshtein import levenshtein


def test_case_1():
    assert levenshtein('electron', 'neutron') == 3


def test_case_2():
    assert levenshtein('kitten', 'sitting') == 3


def test_case_3():
    assert levenshtein('rosettacode', 'raisethysword') == 8


def test_case_4():
    assert levenshtein('abcdefg', 'gabcdef') == 2


def test_case_5():
    assert levenshtein('', '') == 0


def test_case_6():
    assert levenshtein('hello', 'olleh') == 4
