"""Tests für Matrix- und Challenge-Läufe (mit Mock- und Fake-Clients)."""

import csv
import json

from judge_lab import NOTEBOOK_VERSION
from judge_lab.llm import LLMResult, MockClient
from judge_lab.parsing import REPAIR_MESSAGE
from judge_lab.runner import (
    RunContext,
    assignment1_variants,
    prognosis_record,
    run_challenge,
    run_matrix,
    run_one,
)
from judge_lab.scoreboard import RECORD_FIELDS, Scoreboard
from judge_lab.snippets import get_snippet, load_snippets

SNIPPETS = load_snippets()
VALID = json.dumps({"findings": [{"line_start": 26, "category": "bug"}],
                    "scores": {"functional_correctness": 4, "reliability": 5, "maintainability": 6, "readability": 7}})


class ScriptedClient:
    """Liefert nacheinander die vorgegebenen Antworten; merkt sich alle Aufrufe."""

    provider = "mock"
    model_id = "scripted"

    def __init__(self, *answers):
        self.answers = list(answers)
        self.calls = []

    def complete(self, messages):
        self.calls.append(messages)
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer if isinstance(answer, LLMResult) else LLMResult(answer, 0.5, 100, 20)


def ctx(sink=None, model_key="mock"):
    collected = []
    return RunContext(group="Gruppe 1", model_key=model_key, session_id="test",
                      sink=sink or collected.append), collected


def test_matrix_36_records():
    context, sent = ctx()
    progress = []
    attitudes, variants = assignment1_variants("gemini")
    records = run_matrix(context, MockClient(SNIPPETS), SNIPPETS, attitudes, variants,
                         on_progress=lambda done, total: progress.append((done, total)))
    assert len(records) == 36 and len(sent) == 36
    assert progress[-1] == (36, 36)
    assert all(tuple(r) == RECORD_FIELDS for r in records)
    first = records[0]
    assert (first["phase"], first["session_id"], first["group"], first["notebook_version"]) == (
        "a1", "test", "Gruppe 1", NOTEBOOK_VERSION)
    assert first["snippet_id"] == SNIPPETS[0].id and first["attitude"] == "strict" and first["with_tests"] is True


def test_local_matrix_reduced():
    attitudes, variants = assignment1_variants("local")
    assert (attitudes, variants) == (("strict", "lenient"), (False,))
    context, _ = ctx()
    assert len(run_matrix(context, MockClient(SNIPPETS), SNIPPETS, attitudes, variants)) == 12


def test_record_metrics_from_mock():
    context, _ = ctx()
    record = run_one(context, MockClient(SNIPPETS), get_snippet("bank_account"),
                     phase="a1", with_tests=False, attitude="strict")
    assert (record["tp"], record["fp"], record["neutral"], record["n_defects"]) == (1, 1, 1, 6)
    assert record["found_defect_ids"] == "B1"
    assert record["weighted_score"] == 3.0
    assert record["parse_ok"] is True and record["error"] == ""
    assert record["complexity_level"] == ""
    assert record["prompt_text"] == ""


def test_broken_json_marked_not_dropped():
    context, sent = ctx()
    record = run_one(context, MockClient(SNIPPETS), get_snippet("qb_levenshtein"),
                     phase="a1", with_tests=False, attitude="objective")
    assert record["parse_ok"] is False and record["tp"] == 0
    assert record["error"]
    assert sent == [record]


def test_repair_retry_used_once():
    client = ScriptedClient("Sorry, here it is: {broken", VALID)
    context, _ = ctx()
    record = run_one(context, client, get_snippet("bank_account"), phase="a1", with_tests=False, attitude="strict")
    assert record["parse_ok"] is True and record["tp"] == 1
    assert len(client.calls) == 2
    assert client.calls[1][-1] == {"role": "user", "content": REPAIR_MESSAGE}
    assert client.calls[1][-2]["role"] == "assistant"
    assert (record["latency_s"], record["tokens_in"], record["tokens_out"]) == (1.0, 200, 40)


def test_repair_fails_gives_parse_ok_false():
    client = ScriptedClient("nope", "still nope")
    context, _ = ctx()
    record = run_one(context, client, get_snippet("bank_account"), phase="a1", with_tests=False, attitude="strict")
    assert record["parse_ok"] is False and len(client.calls) == 2


def test_llm_error_is_not_counted_as_judge_result():
    # Ein Transportfehler (Key, Limit, Ausfall) sagt nichts über den Judge: keine Treffer-/Recall-Werte.
    client = ScriptedClient(LLMResult("", 1.0, None, None, error="LLM-Aufruf fehlgeschlagen: 429"))
    context, _ = ctx()
    record = run_one(context, client, get_snippet("bank_account"), phase="a1", with_tests=False, attitude="strict")
    assert record["parse_ok"] is None and "429" in record["error"]
    assert (record["tp"], record["fp"], record["recall"], record["precision"]) == (None, None, None, None)
    assert record["n_defects"] == 6
    assert len(client.calls) == 1


def test_client_exception_does_not_abort_matrix():
    client = ScriptedClient(RuntimeError("kaputt"), VALID, VALID)
    context, _ = ctx()
    snippets = [get_snippet("bank_account")]
    records = run_matrix(context, client, snippets, ("strict", "objective", "lenient"), (False,))
    assert len(records) == 3
    failed = [r for r in records if "kaputt" in r["error"]]
    assert len(failed) == 1 and failed[0]["parse_ok"] is None and failed[0]["tp"] is None
    assert sum(1 for r in records if r["parse_ok"]) == 2


def test_challenge_submit_runs_group_and_reference():
    context, sent = ctx(model_key="gemini")
    clients = {"group": MockClient(SNIPPETS), "reference": MockClient(SNIPPETS)}
    records = run_challenge(context, clients, "You are a careful reviewer.", snippets=SNIPPETS,
                            submit=True, submission_no=2)
    assert len(records) == 12 and len(sent) == 12
    submitted = [r for r in records if r["phase"] == "a2_submit"]
    reference = [r for r in records if r["phase"] == "reference"]
    assert len(submitted) == len(reference) == 6
    assert all(r["model_key"] == "gemini" and r["prompt_text"] == "You are a careful reviewer." for r in submitted)
    assert all(r["model_key"] == "reference" and r["prompt_text"] == "" for r in reference)
    assert {r["prompt_hash"] for r in records} == {submitted[0]["prompt_hash"]}
    assert all(r["submission_no"] == 2 and r["with_tests"] is False and r["attitude"] == "custom" for r in records)


def test_challenge_probe_single_snippet():
    context, _ = ctx()
    clients = {"group": MockClient(SNIPPETS), "reference": MockClient(SNIPPETS)}
    records = run_challenge(context, clients, "Be thorough.", snippets=SNIPPETS, submit=False,
                            probe_snippet_id="qb_quicksort")
    assert [(r["phase"], r["snippet_id"]) for r in records] == [("a2_probe", "qb_quicksort")]
    assert records[0]["prompt_text"] == ""


def test_records_have_no_ground_truth_text():
    context, _ = ctx()
    records = run_matrix(context, MockClient(SNIPPETS), SNIPPETS, ("strict",), (True,))
    text = json.dumps(records)
    for snippet in SNIPPETS:
        for defect in snippet.defects:
            assert defect.description not in text


def test_findings_json_is_truncated(monkeypatch):
    many = json.dumps({"findings": [{"line_start": 1, "category": "style", "description": "x" * 500}] * 30})
    context, _ = ctx()
    record = run_one(context, ScriptedClient(many), get_snippet("bank_account"),
                     phase="a1", with_tests=False, attitude="strict")
    assert len(record["findings_json"]) == 5000


def test_prognosis_record():
    context, _ = ctx()
    record = prognosis_record(context, best_model="kimi", strict_vs_lenient="strict findet mehr")
    assert tuple(record) == RECORD_FIELDS
    assert record["phase"] == "prognosis"
    assert record["prediction_best_model"] == "kimi"


def test_end_to_end_csv(tmp_path):
    backup = tmp_path / "backup.csv"
    board = Scoreboard("", "", backup)
    context = RunContext(group="Gruppe 2", model_key="mock", session_id="ci", sink=board.submit)
    run_matrix(context, MockClient(SNIPPETS), SNIPPETS, ("strict", "objective", "lenient"), (True, False))
    with backup.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 36
    assert {r["session_id"] for r in rows} == {"ci"}
    assert {r["parse_ok"] for r in rows} == {"True", "False"}


def test_records_have_unique_run_ids():
    context, _ = ctx()
    records = run_matrix(context, MockClient(SNIPPETS), SNIPPETS, ("strict",), (True, False))
    ids = [r["run_id"] for r in records]
    assert all(ids) and len(set(ids)) == len(ids)


def test_each_submission_has_its_own_id():
    context, _ = ctx(model_key="gemini")
    clients = {"group": MockClient(SNIPPETS), "reference": MockClient(SNIPPETS)}
    first = run_challenge(context, clients, "A", snippets=SNIPPETS, submit=True, submission_no=1)
    # z. B. nach einem Neustart der Laufzeit beginnt der Zähler wieder bei 1
    second = run_challenge(context, clients, "B", snippets=SNIPPETS, submit=True, submission_no=1)
    assert len({r["submission_id"] for r in first}) == 1
    assert first[0]["submission_id"] and first[0]["submission_id"] != second[0]["submission_id"]


def _combinations(model_key, stage):
    from judge_lab.runner import stage_variants

    ids, attitudes, variants = stage_variants(model_key, stage)
    return {(s, a, t) for s in ids for a in attitudes for t in variants}


def test_stage_job_counts_api():
    assert [len(_combinations("gemini", s)) for s in ("judge", "rest", "bonus")] == [3, 15, 18]


def test_stage_job_counts_local():
    assert [len(_combinations("local", s)) for s in ("judge", "rest", "bonus")] == [2, 10, 0]


def test_stage_judge_is_bank_account_without_tests():
    assert {(s, t) for s, _, t in _combinations("deepseek", "judge")} == {("bank_account", False)}


def test_stages_do_not_repeat_each_other():
    for model_key in ("gemini", "local", "local_fallback", "mock"):
        judge, rest, bonus = (_combinations(model_key, s) for s in ("judge", "rest", "bonus"))
        assert not (judge & rest) and not (judge & bonus) and not (rest & bonus)
        # zusammen genau die bisherige Matrix aus Auftrag 1
        assert judge | rest | bonus == _combinations(model_key, "a1")


def test_unknown_stage_rejected():
    import pytest

    from judge_lab.runner import stage_variants

    with pytest.raises(ValueError):
        stage_variants("gemini", "everything")
