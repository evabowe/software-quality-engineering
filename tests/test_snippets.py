"""Tests für die Snippet-Registry und die Konsistenz der Ground Truth."""

import pytest

from judge_lab.snippets import get_snippet, load_snippets

SNIPPETS = load_snippets()


def test_load_finds_bank_account():
    assert "bank_account" in {s.id for s in SNIPPETS}


def test_unknown_snippet_raises_key_error():
    with pytest.raises(KeyError):
        get_snippet("gibt_es_nicht")


def test_numbered_code_format():
    lines = get_snippet("bank_account").numbered_code().splitlines()
    assert lines[25] == " 26 |         self.balance -= amount"
    # Leerzeilen bekommen keine nachgestellten Leerzeichen.
    assert lines[2] == "  3 |"


@pytest.mark.parametrize("snippet", SNIPPETS, ids=lambda s: s.id)
def test_every_meta_is_consistent(snippet):
    code_lines = snippet.code.splitlines()
    assert snippet.defects, "Snippet ohne Ground Truth"
    for d in snippet.defects:
        start, end = d.lines
        a_start, a_end = d.accept_lines
        assert 1 <= a_start <= start <= end <= a_end <= snippet.line_count, d.id
        if d.fix_op == "replace":
            for n in range(start, end + 1):
                assert code_lines[n - 1].strip(), f"{d.id}: Zeile {n} ist leer"


def test_patched_code_removes_bank_defects():
    patched = get_snippet("bank_account").patched_code()
    assert "days" not in patched
    assert "self.balance = self.balance" not in patched
    assert "elif amount < 0" not in patched
    assert "self.balance += amount" in patched
    # Abbuchen vor Gutschrift
    assert patched.index("self.withdraw(amount)") < patched.index("target.deposit(amount)")
