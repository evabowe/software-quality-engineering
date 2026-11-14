"""Tests für die Prompt-Komposition."""

import re
from pathlib import Path

import pytest

from judge_lab.prompts import build_prompt
from judge_lab.snippets import get_snippet, load_snippets

SNIPPETS = load_snippets()
SNAPSHOT = Path(__file__).parent / "snapshots" / "bank_account_prompt.txt"
PROMPT = "Du bist ein strenger Senior-Reviewer."


def _text(messages):
    return "\n".join(m["content"] for m in messages)


def test_messages_structure():
    system, user = build_prompt(get_snippet("qb_quicksort"), PROMPT)
    assert system["role"] == "system" and user["role"] == "user"
    assert system["content"].startswith(PROMPT)
    assert "ISO/IEC 25010" in system["content"]
    assert "  7 |     greater = quicksort([x for x in arr[1:] if x > pivot])" in user["content"]
    assert user["content"].rstrip().endswith('return an empty "findings" list.')


def test_scale_is_a_frame_not_a_rubric():
    # Wie streng bewertet wird, entscheidet der Prompt der Gruppe – die Skala gibt nur Dimensionen und Bereich vor.
    system, _ = build_prompt(get_snippet("qb_bitcount"), PROMPT)
    for dimension in ("functional_correctness", "reliability", "maintainability", "readability"):
        assert dimension in system["content"]
    assert "from 0 to 10" in system["content"]
    assert "Anchors" not in system["content"]
    assert not re.search(r"\b[13579]–\d+\b", system["content"])  # keine Punktebänder wie „5–6“
    assert "40%" not in system["content"]


def test_prompt_is_stripped():
    system, _ = build_prompt(get_snippet("qb_bitcount"), "\n  Sei streng.  \n")
    assert system["content"].startswith("Sei streng.\n")


def test_spec_hint_depends_on_snippet():
    _, bank = build_prompt(get_snippet("bank_account"), PROMPT)
    _, qb = build_prompt(get_snippet("qb_bitcount"), PROMPT)
    assert "module docstring at the top" in bank["content"]
    assert "string block at the end" in qb["content"]


@pytest.mark.parametrize("snippet", SNIPPETS, ids=lambda s: s.id)
def test_no_ground_truth_in_prompt(snippet):
    text = _text(build_prompt(snippet, PROMPT))
    for defect in snippet.defects:
        assert not re.search(rf"\b{defect.id}\b", text)
        assert defect.description not in text
        for line in defect.fix.splitlines():
            if line.strip() and line.strip() not in snippet.code:
                assert line.strip() not in text


@pytest.mark.parametrize("snippet", SNIPPETS, ids=lambda s: s.id)
def test_no_tests_and_no_placeholders_in_prompt(snippet):
    text = _text(build_prompt(snippet, PROMPT))
    assert "def test_" not in text
    assert not re.search(r"\{(spec_hint|code_numbered|tests_block)\}", text)


def test_braces_in_code_survive():
    # str.format würde an den geschweiften Klammern scheitern.
    _, user = build_prompt(get_snippet("qb_shunting_yard"), PROMPT)
    assert "'+': 1," in user["content"]


def test_prompt_snapshot():
    """Bewusste Änderungen am Prompt: Snapshot-Datei löschen, Test laufen lassen, Diff prüfen."""
    text = _text(build_prompt(get_snippet("bank_account"), PROMPT))
    if not SNAPSHOT.exists():
        SNAPSHOT.parent.mkdir(exist_ok=True)
        SNAPSHOT.write_text(text, encoding="utf-8")
        pytest.fail("Snapshot neu erzeugt – bitte prüfen und committen.")
    assert text == SNAPSHOT.read_text(encoding="utf-8")


@pytest.mark.parametrize("snippet", SNIPPETS, ids=lambda s: s.id)
def test_prompt_does_not_name_the_benchmark(snippet):
    # Der Hinweis „QuixBugs“ würde dem Judge verraten, dass genau ein Defekt existiert.
    text = _text(build_prompt(snippet, PROMPT)).lower()
    assert "quixbugs" not in text
    assert "json_testcases" not in text
