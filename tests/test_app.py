"""Tests für die Ein-Zellen-Oberfläche (Reiter, Sperren, Statuszeile)."""

import pytest

from judge_lab import app, ui
from judge_lab.scoreboard import Scoreboard


@pytest.fixture(autouse=True)
def fresh_state(tmp_path, monkeypatch):
    monkeypatch.setattr(ui, "SESSION", ui.Session())
    monkeypatch.setattr(ui, "_scoreboard", lambda: Scoreboard("", "", tmp_path / "backup.csv"))
    monkeypatch.setattr(app, "STATE", app.AppState(phase=0))


def _html(widget) -> str:
    """Alle HTML-Texte eines Widget-Baums (für Prüfungen auf sichtbaren Text)."""
    parts = [getattr(widget, "value", "")] if isinstance(getattr(widget, "value", None), str) else []
    for child in getattr(widget, "children", ()):
        parts.append(_html(child))
    return "\n".join(parts)


def test_all_tabs_exist():
    view = app.build()
    titles = [view.tab.get_title(i) for i in range(len(view.tab.children))]
    assert titles == ["Start", "1 Gutachten", "2 LLM-Judge", "3 Alle Beispiele", "4 Challenge", "5 Abschluss"]


def test_locked_tabs_show_lock_text():
    view = app.build()
    view.set_phase(0)
    assert app.LOCK_TEXT not in _html(view.containers[0])
    for container in view.containers[1:]:
        assert app.LOCK_TEXT in _html(container)


def test_unlock_up_to_phase():
    view = app.build()
    view.set_phase(2)
    assert all(app.LOCK_TEXT not in _html(c) for c in view.containers[:3])
    assert all(app.LOCK_TEXT in _html(c) for c in view.containers[3:])


def test_phase_never_goes_back():
    # Ein versehentlich zurückgesetzter Schalter darf geöffnete Reiter nicht wieder schließen.
    view = app.build()
    view.set_phase(3)
    view.set_phase(1)
    assert app.STATE.phase == 3
    assert app.LOCK_TEXT not in _html(view.containers[3])


def test_status_before_and_after_setup():
    assert "Gruppencode" in app.status_text()
    ui.configure("Gruppe 2", api_key="", mock=True)
    app.STATE.phase = 2
    text = app.status_text()
    assert text.startswith("Gruppe 2 · Judge: Mock")
    assert "Schritt 2 von 5" in text


def test_status_warns_when_runs_stay_local():
    ui.configure("Gruppe 1", api_key="", mock=True)
    ui.SESSION.local_only = 3
    assert "Scoreboard ⚠️" in app.status_text()


def test_short_model_name():
    assert app.judge_name("deepseek") == "DeepSeek"


def test_rebuild_keeps_session_state():
    ui.configure("Gruppe 3", api_key="", mock=True)
    ui.SESSION.submissions_used = 2
    app.build()
    app.build()  # Zelle zweimal ausgeführt
    assert (ui.SESSION.group, ui.SESSION.submissions_used) == ("Gruppe 3", 2)


def test_start_with_code_configures_and_updates_status(monkeypatch):
    monkeypatch.setattr(ui.join, "join", lambda code, **_: ("Gruppe 2", "sk-from-code"))
    view = app.build()
    start = view.start
    start.code.value = " k7q2 "
    start.button.click()
    assert "Ihr seid Gruppe 2" in start.message.value
    assert view.status.value.count("Gruppe 2 · Judge: DeepSeek") == 1


def test_start_unreachable_opens_advanced(monkeypatch):
    def unreachable(code, **_):
        raise ui.join.ServerUnreachable(ui.join.UNREACHABLE)

    monkeypatch.setattr(ui.join, "join", unreachable)
    start = app.build().start
    assert start.advanced.selected_index is None
    start.code.value = "K7Q2"
    start.button.click()
    assert start.advanced.selected_index == 0
    assert "Notfall-Folie" in start.message.value and "Traceback" not in start.message.value


def test_start_unknown_code_keeps_advanced_closed(monkeypatch):
    def unknown(code, **_):
        raise ui.ConfigError("Code unbekannt – bitte den Code noch einmal von der Folie abtippen.")

    monkeypatch.setattr(ui.join, "join", unknown)
    start = app.build().start
    start.code.value = "ZZZZ"
    start.button.click()
    assert start.advanced.selected_index is None
    assert "Code unbekannt" in start.message.value
    assert ui.SESSION.group is None


def test_advanced_opens_when_no_scoreboard_url(monkeypatch):
    monkeypatch.setattr(app, "SCOREBOARD_URL", "")
    assert app.build().start.advanced.selected_index == 0
