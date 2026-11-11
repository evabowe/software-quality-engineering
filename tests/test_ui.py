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
        records, message = ui.submit_challenge(f"You are a careful reviewer, version {number}.")
        assert records and f"{number}/{CHALLENGE_MAX_SUBMISSIONS}" in message
    records, message = ui.submit_challenge("You are a careful reviewer, final version.")
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


def test_queued_double_click_is_ignored():
    # ipywidgets arbeitet Klicks nacheinander ab: der zweite Klick kommt direkt nach dem Ende des ersten an.
    calls, clock = [], [0.0]
    handler = ui._debounced(lambda *_: calls.append(clock[0]), now=lambda: clock[0])
    handler()
    clock[0] = 0.3
    handler()
    clock[0] = 5.0
    handler()
    assert calls == [0.0, 5.0]


def test_same_prompt_is_not_submitted_twice():
    ui.submit_challenge("You are a careful reviewer.")
    records, message = ui.submit_challenge("  You are a careful reviewer.\n")
    assert records is None and "schon eingereicht" in message
    assert ui.SESSION.submissions_used == 1


def test_mock_runs_go_to_separate_session():
    # Probemodus darf weder Leaderboard noch Heatmaps der echten Session verfälschen.
    ui.configure("Gruppe 2", api_key="", mock=True)
    assert ui.SESSION.context().session_id == f"{ui.DEFAULT_SESSION_ID}-mock"
    ui.configure("Gruppe 2", api_key="sk-test")
    assert ui.SESSION.context().session_id == ui.DEFAULT_SESSION_ID


def test_run_stage_judge_only_bank_account():
    records = ui.run_stage("judge")
    assert len(records) == 3
    assert {(r["snippet_id"], r["with_tests"], r["phase"]) for r in records} == {("bank_account", False, "a1")}
    assert ui.SESSION.stage_records["judge"] == records


def test_comparison_table_human_vs_llm():
    ui.submit_human("26, 31", 4, "Einzahlen zieht Geld ab.")
    table = ui.comparison_table(ui.SESSION.human_record, ui.run_stage("judge"))
    assert list(table.index) == ["Ihr (strict)", "LLM strict", "LLM objective", "LLM lenient"]
    assert list(table.columns) == ["Score", "gefunden", "Fehlalarme", "Begründung"]
    assert table.loc["Ihr (strict)", "gefunden"] == "2/6"
    assert table.loc["Ihr (strict)", "Begründung"] == "Einzahlen zieht Geld ab."
    assert table.loc["LLM strict", "gefunden"] == "1/6"
    assert len(table.loc["LLM lenient", "Begründung"]) <= 201


def test_comparison_table_without_human():
    table = ui.comparison_table(None, ui.run_stage("judge"))
    assert table.loc["Ihr", "Begründung"] == "noch kein Gutachten"


def test_comparison_table_has_no_ground_truth():
    ui.submit_human("26", 4, "x")
    text = ui.comparison_table(ui.SESSION.human_record, ui.run_stage("judge")).to_html()
    for defect in SNIPPETS[-1].defects + tuple(d for s in SNIPPETS for d in s.defects):
        assert defect.description not in text


def test_background_stage_finishes_with_complete_records():
    import threading

    done, progress = threading.Event(), []
    result = {}

    def on_done(records, error):
        result.update(records=records, error=error)
        done.set()

    thread = ui.start_stage_in_background("rest", on_progress=lambda d, t: progress.append((d, t)), on_done=on_done)
    thread.join(timeout=30)
    assert done.is_set() and not thread.is_alive()
    assert result["error"] is None and len(result["records"]) == 15
    assert all(r["snippet_id"] != "bank_account" for r in result["records"])
    assert progress[-1] == (15, 15)
    assert "rest" not in ui.SESSION.running


def test_background_stage_cannot_start_twice(monkeypatch):
    import threading

    release = threading.Event()
    monkeypatch.setattr(ui, "run_stage", lambda stage, on_progress=None: release.wait(5) and [])
    thread = ui.start_stage_in_background("rest")
    with pytest.raises(ConfigError, match="laufen schon"):
        ui.start_stage_in_background("rest")
    release.set()
    thread.join(timeout=5)


def test_background_stage_reports_errors(monkeypatch):
    def broken(stage, on_progress=None):
        raise ConfigError("Das lokale Modell läuft noch nicht.")

    monkeypatch.setattr(ui, "run_stage", broken)
    result = {}
    ui.start_stage_in_background("rest", on_done=lambda r, e: result.update(r=r, e=e)).join(timeout=5)
    assert result["r"] is None and "lokale Modell" in str(result["e"])
    assert "rest" not in ui.SESSION.running


def test_a1_records_collect_all_stages():
    ui.run_stage("judge")
    ui.run_stage("rest")
    assert len(ui.SESSION.a1_records) == 18
    table = ui.assignment1_table(ui.SESSION.a1_records)
    assert list(table.index) == [s.title for s in SNIPPETS]


def test_llm_judge_panel_shows_comparison():
    ui.submit_human("26", 4, "Einzahlen zieht Geld ab.")
    panel = ui.llm_judge_panel()
    panel.run.click()
    assert "Ihr (strict)" in panel.result.value and "LLM lenient" in panel.result.value
    assert panel.run.disabled


def test_prognosis_offers_humans():
    assert ("wir Menschen", "human") in ui.best_judge_options()
