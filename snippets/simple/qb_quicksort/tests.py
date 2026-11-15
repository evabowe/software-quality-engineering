"""Tests für quicksort (automatisch erzeugt, Herkunft siehe meta.yaml)."""

from quicksort import quicksort


def test_case_1():
    assert quicksort([1, 2, 6, 72, 7, 33, 4]) == [1, 2, 4, 6, 7, 33, 72]


def test_case_2():
    assert quicksort([3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8, 9, 7, 9, 3]) == [1, 1, 2, 3, 3, 3, 4, 5, 5, 5, 6, 7, 8, 9, 9, 9]


def test_case_3():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]


def test_case_4():
    assert quicksort([5, 4, 3, 1, 2]) == [1, 2, 3, 4, 5]


def test_case_5():
    assert quicksort([8, 1, 14, 9, 15, 5, 4, 3, 7, 17, 11, 18, 2, 12, 16, 13, 6, 10]) == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]


def test_case_6():
    assert quicksort([9, 4, 5, 2, 17, 14, 10, 6, 15, 8, 12, 13, 16, 3, 1, 7, 11]) == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
