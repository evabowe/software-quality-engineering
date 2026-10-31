"""Tests für bitcount.

Automatisch erzeugt von tools/import_quixbugs.py aus QuixBugs
json_testcases/bitcount.json (die ersten 6 Testfälle, die QuixBugs nicht überspringt).
"""

from bitcount import bitcount


def test_case_1():
    assert bitcount(127) == 7


def test_case_2():
    assert bitcount(128) == 1


def test_case_3():
    assert bitcount(3005) == 9


def test_case_4():
    assert bitcount(13) == 3


def test_case_5():
    assert bitcount(14) == 3


def test_case_6():
    assert bitcount(27) == 4
