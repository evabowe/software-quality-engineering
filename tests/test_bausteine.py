"""Tests für die vier Bausteine verbinde, bewerte, bewerte_alle und sende."""

import json
from datetime import datetime

import pytest
import requests

from judge_lab import bausteine
from judge_lab.bausteine import bewerte, bewerte_alle, sende
from judge_lab.llm import ConfigError, LLMResult
from judge_lab.scoreboard import RECORD_FIELDS, Scoreboard

KEYS = {"code_score", "judge_score", "snippet", "komplexitaet", "modell", "prompt", "gruppe", "einreichung", "fehler"}


@pytest.fixture(autouse=True)
def leerer_zustand(monkeypatch):
    monkeypatch.setattr(bausteine, "_ZUSTAND", {"gruppe": "", "key": ""})


class FakeClient:
    """Antwortet immer mit demselben Text bzw. Fehler."""

    provider = "openrouter"
    model_id = "fake/model"

    def __init__(self, text="", error=None, finish_reason="stop"):
        self.text, self.error, self.finish_reason = text, error, finish_reason

    def complete(self, messages):
        return LLMResult(self.text, 0.1, 10, 10, self.error, self.finish_reason)


def use_client(monkeypatch, client):
    monkeypatch.setattr(bausteine, "make_client", lambda modell, key: client)
    bausteine._ZUSTAND.update(gruppe="Gruppe 1", key="sk-test")


# --- verbinde -----------------------------------------------------------------


def test_verbinde_sets_group(monkeypatch, capsys):
    monkeypatch.setattr(bausteine, "_join", lambda code, **kw: ("Gruppe 2", "sk-x"))
    bausteine.verbinde(" k7qx ")
    assert bausteine._ZUSTAND == {"gruppe": "Gruppe 2", "key": "sk-x"}
    assert "Gruppe 2" in capsys.readouterr().out


def test_verbinde_wrong_code_prints_no_traceback(monkeypatch, capsys):
    def fail(code, **kw):
        raise ConfigError("Code unbekannt – bitte den Code noch einmal von der Folie abtippen.")

    monkeypatch.setattr(bausteine, "_join", fail)
    bausteine.verbinde("XXXX")
    assert "Code unbekannt" in capsys.readouterr().out
    assert bausteine._ZUSTAND == {"gruppe": "", "key": ""}


def test_verbinde_notfall_with_key_and_group():
    bausteine.verbinde(key="sk-y", gruppe="Team Rot")
    assert bausteine._ZUSTAND == {"gruppe": "Team Rot", "key": "sk-y"}


def test_verbinde_notfall_needs_both(capsys):
    bausteine.verbinde(key="sk-y")
    assert "gruppe" in capsys.readouterr().out
    assert bausteine._ZUSTAND == {"gruppe": "", "key": ""}


def test_verbinde_again_switches_group(monkeypatch):
    answers = iter([("Gruppe 1", "sk-1"), ("Gruppe 3", "sk-3")])
    monkeypatch.setattr(bausteine, "_join", lambda code, **kw: next(answers))
    bausteine.verbinde("AAAA")
    bausteine.verbinde("BBBB")
    assert bausteine._ZUSTAND == {"gruppe": "Gruppe 3", "key": "sk-3"}


# --- bewerte ------------------------------------------------------------------


def test_bewerte_mock_returns_both_scores():
    r = bewerte("Sei streng.", snippet="bank_account", modell="mock")
    assert r["fehler"] is None and r["code_score"] == 6.0 and r["judge_score"] == 1  # Mock: 1 Treffer, 1 Fehlalarm
    assert set(r) == KEYS
    assert (r["snippet"], r["komplexitaet"], r["modell"], r["prompt"]) == ("bank_account", "", "mock", "Sei streng.")


def test_bewerte_default_model_is_gpt6_luna(monkeypatch):
    seen = []
    monkeypatch.setattr(bausteine, "make_client", lambda modell, key: seen.append(modell) or FakeClient("{}"))
    bausteine._ZUSTAND.update(gruppe="Gruppe 1", key="sk-test")
    assert bewerte("x")["modell"] == "openai/gpt-6-luna"
    assert seen == ["openai/gpt-6-luna"]


def test_bewerte_unknown_snippet_lists_valid_names():
    r = bewerte("x", snippet="quicksort", modell="mock")
    assert r["code_score"] is None and r["judge_score"] is None
    assert "qb_quicksort" in r["fehler"] and "bank_account" in r["fehler"]


def test_bewerte_without_verbinde_gives_hint():
    r = bewerte("x")
    assert "verbinde" in r["fehler"] and r["judge_score"] is None


def test_bewerte_empty_prompt():
    assert "leer" in bewerte("  ", modell="mock")["fehler"]


def test_bewerte_llm_error_is_not_zero(monkeypatch, capsys):
    use_client(monkeypatch, FakeClient(error="LLM-Aufruf fehlgeschlagen: 401 invalid key"))
    r = bewerte("x")
    assert r["judge_score"] is None and r["code_score"] is None
    assert "nicht erreichbar" in r["fehler"] and "401" in r["fehler"]
    assert "bank_account" in capsys.readouterr().out


def test_bewerte_unreadable_answer(monkeypatch):
    use_client(monkeypatch, FakeClient("das ist kein JSON"))
    r = bewerte("x")
    assert r["judge_score"] is None and "nicht lesbar" in r["fehler"]


def test_bewerte_missing_dimension_keeps_judge_score(monkeypatch):
    answer = {"findings": [{"line_start": 1, "line_end": 1, "category": "bug"}],
              "scores": {"functional_correctness": 4, "reliability": 5, "maintainability": 6}}
    use_client(monkeypatch, FakeClient(json.dumps(answer)))
    r = bewerte("x", snippet="qb_bitcount")
    assert r["code_score"] is None and r["judge_score"] is not None and r["fehler"] is None


def test_bewerte_uses_no_tests_in_prompt(monkeypatch):
    calls = []
    original = bausteine.build_prompt
    monkeypatch.setattr(bausteine, "build_prompt", lambda *a, **kw: calls.append(kw) or original(*a, **kw))
    bewerte("Sei streng.", modell="mock")
    assert calls == [{"with_tests": False, "custom_block": "Sei streng."}]


def test_bewerte_each_call_is_its_own_submission():
    assert bewerte("x", modell="mock")["einreichung"] != bewerte("x", modell="mock")["einreichung"]


# --- bewerte_alle -------------------------------------------------------------


def test_bewerte_alle_five_snippets_sorted_and_one_submission():
    rs = bewerte_alle("Sei streng.", modell="mock")
    assert [r["komplexitaet"] for r in rs] == ["L1", "L2", "L3", "L4", "L5"]
    assert [r["snippet"] for r in rs] == ["qb_bitcount", "qb_quicksort", "qb_levenshtein",
                                          "qb_shunting_yard", "qb_next_permutation"]
    assert len({r["einreichung"] for r in rs}) == 1
    assert all(set(r) == KEYS for r in rs)


def test_bewerte_alle_one_failure_keeps_others():
    rs = bewerte_alle("x", modell="mock")  # Mock: qb_levenshtein liefert immer kaputtes JSON
    assert rs[2]["snippet"] == "qb_levenshtein" and rs[2]["fehler"]
    assert all(r["fehler"] is None for i, r in enumerate(rs) if i != 2)


def test_bewerte_alle_without_verbinde_gives_hint():
    rs = bewerte_alle("x")
    assert len(rs) == 5 and all("verbinde" in r["fehler"] for r in rs)


@pytest.mark.parametrize("antwort", [
    '{"findings": [{"line_start": 3, "line_end": 3, "category": "bug"}, {"line_start": ',  # bei MAX_TOKENS abgeschnitten
    '{"error": "I cannot help with that."}',                                                 # Ablehnung im JSON-Modus
])
def test_bewerte_answer_without_findings_and_scores_is_unreadable(monkeypatch, antwort):
    use_client(monkeypatch, FakeClient(antwort))
    r = bewerte("x")
    assert r["judge_score"] is None and r["code_score"] is None and "nicht lesbar" in r["fehler"]


def test_bewerte_truncated_answer_says_so(monkeypatch):
    use_client(monkeypatch, FakeClient('{"findings": [{"line_start": 3', finish_reason="length"))
    r = bewerte("x")
    assert r["judge_score"] is None and "abgeschnitten" in r["fehler"]


# --- sende -------------------------------------------------------------------


def ergebnis(**overrides):
    base = {"code_score": 5.2, "judge_score": 3, "snippet": "bank_account", "komplexitaet": "",
            "modell": "openai/gpt-6-luna", "prompt": "Sei streng.", "gruppe": "Gruppe 2",
            "einreichung": "e1", "fehler": None}
    return {**base, **overrides}


def fuenf(**overrides):
    namen = ["qb_bitcount", "qb_quicksort", "qb_levenshtein", "qb_shunting_yard", "qb_next_permutation"]
    return [ergebnis(snippet=n, komplexitaet=f"L{i + 1}", **overrides) for i, n in enumerate(namen)]


class FakeBoard:
    def __init__(self, ok=True):
        self.ok, self.calls, self.last_error = ok, [], ""

    def replay_backup(self):
        return 0

    def submit(self, records):
        self.calls.append(records)
        return self.ok


@pytest.fixture
def board(monkeypatch):
    fake = FakeBoard()
    monkeypatch.setattr(bausteine, "_scoreboard", lambda: fake)
    return fake


def test_sende_round2_single_result(board, capsys):
    assert sende(ergebnis(), runde=2) is True
    [rows] = board.calls
    assert len(rows) == 1 and tuple(rows[0]) == RECORD_FIELDS
    row = rows[0]
    assert (row["runde"], row["gruppe"], row["snippet"], row["code_score"], row["judge_score"]) == \
        (2, "Gruppe 2", "bank_account", 5.2, 3)
    assert len(row["run_id"]) == 32
    assert datetime.fromisoformat(row["timestamp"]).utcoffset().total_seconds() == 0
    assert "gesendet" in capsys.readouterr().out


def test_sende_round4_list_sends_five_in_one_call(board):
    assert sende(fuenf(), runde=4) is True
    assert len(board.calls) == 1 and len(board.calls[0]) == 5
    assert len({r["run_id"] for r in board.calls[0]}) == 5
    assert {r["einreichung"] for r in board.calls[0]} == {"e1"}


def test_sende_list_in_round1_is_rejected(board, capsys):
    assert sende(fuenf(), runde=1) is False
    assert board.calls == [] and "bewerte(" in capsys.readouterr().out


def test_sende_single_in_round3_is_rejected(board, capsys):
    assert sende(ergebnis(), runde=3) is False
    assert board.calls == [] and "bewerte_alle" in capsys.readouterr().out


@pytest.mark.parametrize("runde", [0, 5, "2", True, None])
def test_sende_invalid_round(board, capsys, runde):
    assert sende(ergebnis(), runde=runde) is False
    assert board.calls == [] and "1–4" in capsys.readouterr().out


def test_sende_skips_failed_and_reports(board, capsys):
    rs = fuenf()
    rs[2] = ergebnis(snippet="qb_levenshtein", komplexitaet="L3", code_score=None, judge_score=None,
                     fehler="Die Antwort des Modells war nicht lesbar")
    assert sende(rs, runde=3) is True
    assert [r["snippet"] for r in board.calls[0]] == ["qb_bitcount", "qb_quicksort", "qb_shunting_yard",
                                                      "qb_next_permutation"]
    assert "qb_levenshtein" in capsys.readouterr().out


def test_sende_only_failed_sends_nothing(board, capsys):
    assert sende(ergebnis(fehler="kaputt", code_score=None, judge_score=None), runde=1) is False
    assert board.calls == []


def test_sende_skips_mock(board, capsys):
    assert sende(ergebnis(modell="mock"), runde=1) is False
    assert board.calls == [] and "Mock-Ergebnisse gehen nicht ans Dashboard" in capsys.readouterr().out


def test_sende_offline_message(monkeypatch, capsys):
    monkeypatch.setattr(bausteine, "_scoreboard", lambda: FakeBoard(ok=False))
    assert sende(ergebnis(), runde=1) is False
    assert "lokal gesichert" in capsys.readouterr().out


def test_sende_replays_backup_first(monkeypatch, tmp_path):
    sent = []
    state = {"online": False}

    def post(url, json=None, timeout=None):
        if not state["online"]:
            raise requests.ConnectionError("offline")
        sent.append(json["records"])

        class Ok:
            status_code = 200

            def json(self):
                return {"status": "ok"}

        return Ok()

    real = Scoreboard("https://example.test/exec", "tok", tmp_path / "backup.csv", post=post)
    monkeypatch.setattr(bausteine, "_scoreboard", lambda: real)
    assert sende(fuenf(), runde=4) is False
    assert (tmp_path / "backup.csv").exists()
    state["online"] = True
    assert sende(ergebnis(), runde=1) is True
    assert not (tmp_path / "backup.csv").exists()
    assert [len(batch) for batch in sent] == [5, 1]


def test_sende_twice_gives_same_run_ids(board):
    rs = fuenf()
    sende(rs, runde=4)
    sende(rs, runde=4)
    first, second = board.calls
    assert [r["run_id"] for r in first] == [r["run_id"] for r in second]
    assert len({r["run_id"] for r in first}) == 5


def test_sende_same_result_other_round_gets_other_run_id(board):
    sende(ergebnis(), runde=1)
    sende(ergebnis(), runde=2)
    assert board.calls[0][0]["run_id"] != board.calls[1][0]["run_id"]


@pytest.mark.parametrize("falsch", [None, "text", [None], [ergebnis(), 3]])
def test_sende_wrong_type_gives_hint_not_traceback(board, capsys, falsch):
    runde = 3 if isinstance(falsch, list) else 1
    assert sende(falsch, runde=runde) is False
    assert board.calls == [] and "bewerte" in capsys.readouterr().out


def test_sende_shows_server_refusal(monkeypatch, capsys, tmp_path):
    class Refused:
        status_code = 200

        def json(self):
            return {"status": "error", "message": "Tab runs hat eine alte Kopfzeile – bitte in runs_alt umbenennen"}

    real = Scoreboard("https://example.test/exec", "tok", tmp_path / "backup.csv", post=lambda *a, **k: Refused())
    monkeypatch.setattr(bausteine, "_scoreboard", lambda: real)
    assert sende(ergebnis(), runde=1) is False
    assert "alte Kopfzeile" in capsys.readouterr().out


# --- öffentliche Schnittstelle ------------------------------------------------


def test_public_api_is_exactly_four():
    import judge_lab

    public = sorted(n for n in dir(judge_lab) if not n.startswith("_") and callable(getattr(judge_lab, n)))
    assert public == ["bewerte", "bewerte_alle", "sende", "verbinde"]
