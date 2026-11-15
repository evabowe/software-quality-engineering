"""Tests für next_permutation (automatisch erzeugt, Herkunft siehe meta.yaml)."""

from next_permutation import next_permutation


def test_case_1():
    assert next_permutation([3, 2, 4, 1]) == [3, 4, 1, 2]


def test_case_2():
    assert next_permutation([3, 5, 6, 2, 1]) == [3, 6, 1, 2, 5]


def test_case_3():
    assert next_permutation([3, 5, 6, 2]) == [3, 6, 2, 5]


def test_case_4():
    assert next_permutation([4, 5, 1, 7, 9]) == [4, 5, 1, 9, 7]


def test_case_5():
    assert next_permutation([4, 5, 8, 7, 1]) == [4, 7, 1, 5, 8]


def test_case_6():
    assert next_permutation([9, 5, 2, 6, 1]) == [9, 5, 6, 1, 2]
