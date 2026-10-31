"""Prüft, dass das Paket die Datenordner im Repository findet."""

from judge_lab import config


def test_paths_exist():
    assert (config.SNIPPETS_DIR / "bank_account" / "bank_account.py").is_file()
    assert (config.PROMPTS_DIR / "original" / "SOURCE.md").is_file()
