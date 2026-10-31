"""Tests für die Prompt-Komposition und den Challenge-Lint."""

import re
from pathlib import Path

import pytest

from judge_lab.config import ATTITUDES, PROMPTS_DIR
from judge_lab.prompts import build_prompt, lint_challenge_prompt, prompt_hash
from judge_lab.snippets import get_snippet, load_snippets

SNIPPETS = load_snippets()
SNAPSHOT = Path(__file__).parent / "snapshots" / "bank_account_objective_with_tests.txt"


def _text(messages):
    return "\n".join(m["content"] for m in messages)


def test_messages_structure():
    system, user = build_prompt(get_snippet("qb_quicksort"), attitude="strict", with_tests=False)
    assert system["role"] == "system" and user["role"] == "user"
    assert "Chief Embedded Software Architect" in system["content"]
    assert "ISO/IEC 25010" in system["content"]
    assert "  7 |     greater = quicksort([x for x in arr[1:] if x > pivot])" in user["content"]
    assert user["content"].rstrip().endswith('return an empty "findings" list.')


def test_spec_hint_depends_on_snippet():
    _, bank = build_prompt(get_snippet("bank_account"), attitude="objective", with_tests=False)
    _, qb = build_prompt(get_snippet("qb_bitcount"), attitude="objective", with_tests=False)
    assert "module docstring at the top" in bank["content"]
    assert "string block at the end" in qb["content"]


@pytest.mark.parametrize("with_tests", [True, False])
@pytest.mark.parametrize("attitude", ATTITUDES)
@pytest.mark.parametrize("snippet", SNIPPETS, ids=lambda s: s.id)
def test_no_ground_truth_in_prompt(snippet, attitude, with_tests):
    text = _text(build_prompt(snippet, attitude=attitude, with_tests=with_tests))
    for defect in snippet.defects:
        assert not re.search(rf"\b{defect.id}\b", text)
        assert defect.description not in text
        for line in defect.fix.splitlines():
            if line.strip() and line.strip() not in snippet.code:
                assert line.strip() not in text


def test_braces_in_code_survive():
    # str.format würde an den geschweiften Klammern scheitern.
    _, user = build_prompt(get_snippet("qb_shunting_yard"), attitude="lenient", with_tests=True)
    assert "'+': 1," in user["content"]
    assert "{code_numbered}" not in user["content"]


def test_tests_block_toggle():
    snippet = get_snippet("qb_quicksort")
    _, with_tests = build_prompt(snippet, attitude="objective", with_tests=True)
    _, without = build_prompt(snippet, attitude="objective", with_tests=False)
    assert "def test_case_1" in with_tests["content"]
    assert "expected behavior" in with_tests["content"]
    assert "def test_case_1" not in without["content"]
    assert "expected behavior" not in without["content"]
    assert "{tests_block}" not in without["content"]


def test_custom_block_replaces_attitude():
    system, _ = build_prompt(get_snippet("qb_bitcount"), custom_block="You are a careful reviewer.", with_tests=False)
    assert system["content"].startswith("You are a careful reviewer.")
    assert "Senior System Engineer" not in system["content"]
    assert "ISO/IEC 25010" in system["content"]


@pytest.mark.parametrize("kwargs", [{}, {"attitude": "strict", "custom_block": "x"}])
def test_exactly_one_block_required(kwargs):
    with pytest.raises(ValueError):
        build_prompt(get_snippet("qb_bitcount"), with_tests=False, **kwargs)


def test_unknown_attitude_rejected():
    with pytest.raises(ValueError):
        build_prompt(get_snippet("qb_bitcount"), attitude="grumpy", with_tests=False)


def test_prompt_hash_stable():
    assert prompt_hash("  Be strict.\n") == prompt_hash("Be strict.")
    assert len(prompt_hash("Be strict.")) == 12
    assert prompt_hash("Be strict.") != prompt_hash("Be lenient.")


@pytest.mark.parametrize("text", ["Check line 7 carefully.", "Achte auf Zeile 26!", "siehe Z. 5"])
def test_lint_warns_on_line_numbers(text):
    assert lint_challenge_prompt(text, SNIPPETS)


def test_lint_warns_on_function_names():
    warnings = lint_challenge_prompt("Look closely at quicksort and BankAccount.", SNIPPETS)
    assert any("quicksort" in w and "BankAccount" in w for w in warnings)


def test_lint_baseline_clean():
    baseline = (PROMPTS_DIR / "challenge_baseline.md").read_text(encoding="utf-8")
    assert lint_challenge_prompt(baseline, SNIPPETS) == []


def test_prompt_snapshot():
    """Bewusste Änderungen am Prompt: Snapshot-Datei löschen, Test laufen lassen, Diff prüfen."""
    text = _text(build_prompt(get_snippet("bank_account"), attitude="objective", with_tests=True))
    if not SNAPSHOT.exists():
        SNAPSHOT.parent.mkdir(exist_ok=True)
        SNAPSHOT.write_text(text, encoding="utf-8")
        pytest.fail("Snapshot neu erzeugt – bitte prüfen und committen.")
    assert text == SNAPSHOT.read_text(encoding="utf-8")


@pytest.mark.parametrize("snippet", SNIPPETS, ids=lambda s: s.id)
def test_prompt_does_not_name_the_benchmark(snippet):
    # Der Hinweis „QuixBugs“ würde dem Judge verraten, dass genau ein Defekt existiert.
    text = _text(build_prompt(snippet, attitude="objective", with_tests=True)).lower()
    assert "quixbugs" not in text
    assert "json_testcases" not in text
