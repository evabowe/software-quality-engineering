"""Tests für Schritt 1: das menschliche Gutachten (Eingabe, Messung, Rückmeldung ohne Ground Truth)."""

import json

import pytest

from judge_lab import human, ui
from judge_lab.config import HUMAN_ROLES, HUMAN_SNIPPET
from judge_lab.runner import RunContext
from judge_lab.scoreboard import RECORD_FIELDS, Scoreboard
from judge_lab.snippets import get_snippet

SNIPPET = get_snippet(HUMAN_SNIPPET)


def spans(findings):
    return [(f.line_start, f.line_end) for f in findings]


@pytest.mark.parametrize("text, expected", [
    ("26, 31, 39-40", [(26, 26), (31, 31), (39, 40)]),
    ("26;31 32", [(26, 26), (31, 31), (32, 32)]),
    ("39–40", [(39, 40)]),  # Gedankenstrich aus Word/Folie
    (" 39 - 40 ", [(39, 40)]),
    ("31, 26, 26", [(26, 26), (31, 31)]),  # Duplikate zählen einmal, sortiert
    ("26,\n31", [(26, 26), (31, 31)]),
])
def test_parse_lines(text, expected):
    findings = human.parse_lines(text, SNIPPET.line_count)
    assert spans(findings) == expected
    assert {f.category for f in findings} == {"bug"}


@pytest.mark.parametrize("text", ["keine", " Keine ", "-"])
def test_parse_lines_explicit_none(text):
    assert human.parse_lines(text, SNIPPET.line_count) == []


@pytest.mark.parametrize("text, message", [
    ("", "mindestens eine Zeile"),
    ("abc", "„abc“"),
    ("26, Zeile 31", "„Zeile“"),
    ("0", "Zeile 0 gibt es nicht"),
    ("26, 101", "Zeile 101 gibt es nicht"),
    ("40-39", "40-39"),
    ("3-", "„3-“"),
])
def test_parse_lines_rejects_nonsense(text, message):
    with pytest.raises(human.InputError, match=message):
        human.parse_lines(text, 100)


def test_role_cards_for_all_groups():
    cards = human.load_role_cards()
    assert set(cards) == {"strict", "objective", "lenient", "none"}
    assert cards["none"] == "Bewertet nach eurem eigenen Urteil."
    assert "3" in cards["strict"] and "7" in cards["lenient"]
    for card in cards.values():
        assert len(card.splitlines()) <= 5
    assert human.role_card("Gruppe 4") == cards["none"]
    assert human.role_card("Gruppe 1") == cards[HUMAN_ROLES["Gruppe 1"]]


def test_human_record():
    sent = []
    ctx = RunContext(group="Gruppe 3", model_key="kimi", session_id="test", sink=sent.append)
    findings = human.parse_lines("26, 31, 60", SNIPPET.line_count)
    record = human.human_record(ctx, findings, score=4, justification="Einzahlen zieht Geld ab.")
    assert sent == [record] and tuple(record) == RECORD_FIELDS
    assert (record["phase"], record["model_key"], record["model_id"], record["attitude"]) == (
        "human", "human", "human", "lenient")
    assert (record["snippet_id"], record["weighted_score"], record["with_tests"]) == (HUMAN_SNIPPET, 4, False)
    assert (record["tp"], record["n_defects"], record["parse_ok"]) == (2, 6, True)
    assert record["fp"] == 1 and record["recall"] == pytest.approx(2 / 6)
    stored = json.loads(record["findings_json"])
    assert stored["justification"] == "Einzahlen zieht Geld ab."
    assert [(f["line_start"], f["line_end"]) for f in stored["findings"]] == [(26, 26), (31, 31), (60, 60)]


def test_control_group_has_role_none():
    ctx = RunContext(group="Gruppe 4", model_key="local", session_id="test", sink=lambda r: None)
    assert human.human_record(ctx, [], score=5, justification="x")["attitude"] == "none"


@pytest.mark.parametrize("tp, fp, expected", [
    (2, 1, "Ihr habt 2 von 6 Defekten gefunden, 1 Meldung war kein Defekt."),
    (1, 0, "Ihr habt 1 von 6 Defekten gefunden, 0 Meldungen waren keine Defekte."),
    (0, 3, "Ihr habt 0 von 6 Defekten gefunden, 3 Meldungen waren keine Defekte."),
])
def test_feedback_counts_only(tp, fp, expected):
    assert human.feedback({"tp": tp, "fp": fp, "n_defects": 6}) == expected


@pytest.fixture
def session(tmp_path, monkeypatch):
    monkeypatch.setattr(ui, "SESSION", ui.Session())
    monkeypatch.setattr(ui, "_scoreboard", lambda: Scoreboard("", "", tmp_path / "backup.csv"))
    ui.configure("Gruppe 1", api_key="", mock=True)
    return ui.SESSION


def test_submit_human_once(session):
    record, message = ui.submit_human("26, 31", 3, "Zu viele Fehler.")
    assert record["attitude"] == "strict" and "2 von 6" in message
    again, message = ui.submit_human("26", 5, "Doch nicht.")
    assert again is None and "schon abgegeben" in message
    corrected, _ = ui.submit_human("26", 5, "Doch nicht.", correction=True)
    assert corrected["tp"] == 1 and session.human_record is corrected


def test_submit_human_needs_justification(session):
    record, message = ui.submit_human("26", 3, "  ")
    assert record is None and "Begründung" in message and session.human_record is None


def _texts(widget):
    value = getattr(widget, "value", None)
    parts = [value] if isinstance(value, str) else []
    for child in getattr(widget, "children", ()):
        parts.append(_texts(child))
    return "\n".join(parts)


def test_human_panel_hides_ground_truth(session):
    panel = ui.human_panel()
    panel.lines.value = "26, 31, 39-40"
    panel.justification.value = "Kontostand stimmt nach Einzahlung nicht."
    panel.submit.click()
    shown = _texts(panel.widget)
    assert "Nicht verraten!" in shown and "von 6 Defekten" in shown
    assert panel.submit.disabled and "abgegeben" in panel.submit.description
    for defect in SNIPPET.defects:
        assert defect.description not in shown
        assert defect.id not in shown  # keine Defekt-IDs
