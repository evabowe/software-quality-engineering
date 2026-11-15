"""Tests für shunting_yard (automatisch erzeugt, Herkunft siehe meta.yaml)."""

from shunting_yard import shunting_yard


def test_case_1():
    assert shunting_yard([]) == []


def test_case_2():
    assert shunting_yard([30]) == [30]


def test_case_3():
    assert shunting_yard([10, '-', 5, '-', 2]) == [10, 5, '-', 2, '-']


def test_case_4():
    assert shunting_yard([34, '-', 12, '/', 5]) == [34, 12, 5, '/', '-']


def test_case_5():
    assert shunting_yard([4, '+', 9, '*', 9, '-', 10, '+', 13]) == [4, 9, 9, '*', '+', 10, '-', 13, '+']


def test_case_6():
    assert shunting_yard([7, '*', 43, '-', 7, '+', 13, '/', 7]) == [7, 43, '*', 7, '-', 13, 7, '/', '+']
