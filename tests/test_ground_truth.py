"""Plausibilisierung der Ground Truth.

Für jedes Snippet gilt: Die Original-Tests schlagen auf dem Code fehl und
laufen grün, sobald alle in ``meta.yaml`` dokumentierten Korrekturen
angewendet sind. Damit sind Zeilennummern und Korrekturen maschinell geprüft.
"""

import hashlib

import pytest

from judge_lab.snippets import get_snippet, load_snippets
from snippet_runner import run_snippet_tests

SNIPPETS = load_snippets()
QUIXBUGS = [s for s in SNIPPETS if s.source.get("name") == "QuixBugs"]


@pytest.mark.parametrize("snippet", SNIPPETS, ids=lambda s: s.id)
def test_original_code_fails(snippet, tmp_path):
    outcome = run_snippet_tests(snippet, snippet.code, tmp_path)
    assert outcome.failed > 0 or outcome.timed_out


@pytest.mark.parametrize("snippet", SNIPPETS, ids=lambda s: s.id)
def test_patched_code_passes(snippet, tmp_path):
    outcome = run_snippet_tests(snippet, snippet.patched_code(), tmp_path)
    assert not outcome.timed_out
    assert outcome.failed == 0
    assert outcome.passed > 0


@pytest.mark.parametrize("snippet", QUIXBUGS, ids=lambda s: s.id)
def test_quixbugs_source_unchanged(snippet):
    data = (snippet.folder / snippet.code_file).read_bytes()
    assert hashlib.sha256(data).hexdigest() == snippet.source["sha256"]


def test_bank_account_fails_as_documented(tmp_path):
    # SOLUTION.md: 4 von 20 Tests schlagen fehl.
    snippet = get_snippet("bank_account")
    outcome = run_snippet_tests(snippet, snippet.code, tmp_path)
    assert (outcome.failed, outcome.passed) == (4, 16)
