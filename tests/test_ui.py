"""Tests für die Notebook-Oberfläche (Aktionen und Tabellen; Widgets nur als Smoke-Test)."""

import pytest
import requests

from judge_lab import ui
from judge_lab.config import CHALLENGE_MAX_SUBMISSIONS
from judge_lab.llm import ConfigError
from judge_lab.scoreboard import Scoreboard
from judge_lab.snippets import load_snippets

SNIPPETS = load_snippets()


@pytest.fixture(autouse=True)
def mock_session(tmp_path, monkeypatch):
    """Frische Session im Probemodus; Scoreboard schreibt nur in eine temporäre CSV."""
    monkeypatch.setattr(ui, "SESSION", ui.Session())
    monkeypatch.setattr(ui, "_scoreboard", lambda: Scoreboard("", "", tmp_path / "backup.csv"))
    ui.configure("Gruppe 1", api_key="", mock=True)
    return ui.SESSION


def test_configure_sets_group_model():
    session = ui.SESSION
    ui.configure("Gruppe 3", api_key="sk-test")
    assert (session.group, session.model_key, session.mock) == ("Gruppe 3", "kimi", False)


def test_configure_without_key_fails_with_german_message():
    with pytest.raises(ConfigError, match="API-Key"):
        ui.configure("Gruppe 2", api_key="")


def test_configure_fallback_for_group_4():
    ui.configure("Gruppe 4", api_key="sk-test", use_fallback=True)
    assert ui.SESSION.model_key == "local_fallback"


def test_run_assignment1_mock():
    records = ui.run_assignment1()
    assert len(records) == 36
    assert ui.SESSION.a1_records == records


def test_table_shows_counts_not_locations():
    records = ui.run_assignment1()
    table = ui.assignment1_table(records)
    assert list(table.index) == [s.title for s in SNIPPETS]
    assert "strict · mit Tests" in table.columns
    assert table.loc["Bankkonto", "strict · ohne Tests"] == "3.0 · 1/6"
    html = table.to_html()
    for snippet in SNIPPETS:
        for defect in snippet.defects:
            assert defect.description not in html
            assert defect.id not in html


def test_unreadable_answer_is_marked_in_table():
    table = ui.assignment1_table(ui.run_assignment1())
    levenshtein = next(s.title for s in SNIPPETS if s.id == "qb_levenshtein")
    assert "unlesbar" in table.loc[levenshtein, "objective · mit Tests"]


def test_submit_counts_and_blocks_after_max():
    for number in range(1, CHALLENGE_MAX_SUBMISSIONS + 1):
        records, message = ui.submit_challenge("You are a careful reviewer.")
        assert records and f"{number}/{CHALLENGE_MAX_SUBMISSIONS}" in message
    records, message = ui.submit_challenge("You are a careful reviewer.")
    assert records is None and "keine Einreichung mehr" in message
    assert ui.SESSION.submissions_used == CHALLENGE_MAX_SUBMISSIONS


def test_empty_prompt_is_not_submitted():
    records, message = ui.submit_challenge("   ")
    assert records is None and ui.SESSION.submissions_used == 0


def test_probe_does_not_count():
    records, _ = ui.probe_challenge("Be thorough.", "qb_quicksort")
    assert len(records) == 1 and ui.SESSION.submissions_used == 0


def test_challenge_summary():
    records, _ = ui.submit_challenge("You are a careful reviewer.")
    summary = ui.challenge_summary(records)
    assert list(summary.columns) == ["Treffer", "Fehlalarme", "Punkte", "Punkte Referenz"]
    assert summary.loc["Bankkonto", "Treffer"] == "✔ 1/6"
    assert summary.loc["Summe", "Punkte"] == 5


def test_panels_construct_and_counter_survives_rerun():
    ui.submit_challenge("You are a careful reviewer.")
    for _ in range(2):  # Zelle zweimal ausgeführt
        for panel in (ui.setup_panel(), ui.prognosis_panel(), ui.snippet_viewer(),
                      ui.assignment1_panel(), ui.assignment2_panel()):
            assert panel is not None
    assert ui.SESSION.submissions_used == 1
    assert "2/3" in ui._submit_label()


def test_snippet_view_has_no_ground_truth():
    for snippet in SNIPPETS:
        html = ui.snippet_html(snippet.id)
        assert "1 |" in html
        for defect in snippet.defects:
            assert defect.description not in html


@pytest.mark.parametrize(
    "exc, expected",
    [(ConfigError("Es fehlt der OpenRouter-API-Key."), "API-Key"),
     (requests.ConnectionError("x"), "Verbindung"),
     (RuntimeError("boom"), "RuntimeError")],
)
def test_friendly_error(exc, expected):
    message = ui.friendly_error(exc)
    assert expected in message and "Traceback" not in message


class FailingClient:
    provider = "mock"
    model_id = "failing"

    def complete(self, messages):
        from judge_lab.llm import LLMResult

        return LLMResult("", 0.1, None, None, error="LLM-Aufruf fehlgeschlagen: Error code: 401 - User not found")


def test_infrastructure_error_shown_as_error(monkeypatch):
    monkeypatch.setattr(ui.Session, "client", lambda self: FailingClient())
    records = ui.run_assignment1()
    table = ui.assignment1_table(records)
    assert table.iloc[0, 0] == "Fehler"
    assert any("401" in line for line in ui.error_summary(records))
    summary_records, _ = ui.submit_challenge("Be careful.")
    assert ui.challenge_summary(summary_records).iloc[0]["Treffer"] == "Fehler"


def test_ollama_not_running_gives_german_message(monkeypatch):
    ui.configure("Gruppe 4", api_key="sk-test")
    monkeypatch.setattr(ui.ollama_colab, "is_up", lambda: False)
    with pytest.raises(ConfigError, match="Gruppe 4"):
        ui.SESSION.client()


def test_warns_when_runs_are_only_saved_locally():
    # Das Fixture-Scoreboard hat keine URL: jeder Lauf landet nur in der CSV.
    assert ui.local_only_warning(0) is None
    before = ui.SESSION.local_only
    ui.run_assignment1()
    warning = ui.local_only_warning(before)
    assert "36 Läufe" in warning and "lokal" in warning
    assert ui.SESSION.local_only == before + 36
