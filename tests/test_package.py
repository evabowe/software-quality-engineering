"""Prüft, dass das Paket die Datenordner im Repository findet."""

from judge_lab import config


def test_paths_exist():
    assert (config.SNIPPETS_DIR / "simple" / "bank_account" / "bank_account.py").is_file()
    assert (config.PROMPTS_DIR / "scale_iso25010.md").is_file()
