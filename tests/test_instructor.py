"""Tests für die Hilfsfunktionen des Instructor-Notebooks."""

from judge_lab import instructor
from judge_lab.llm import MockClient
from judge_lab.runner import RunContext, run_matrix
from judge_lab.snippets import load_snippets


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload, self.status_code = payload, status

    def json(self):
        return self.payload


def test_ground_truth_rows():
    rows = instructor.ground_truth_rows()
    assert len(rows) == 11
    assert {"snippet_id": "qb_shunting_yard", "defect_id": "D1", "kind": "bug", "lines": "17–18"}.items() <= next(
        r for r in rows if r["snippet_id"] == "qb_shunting_yard").items()


def test_upload_ground_truth_posts_defects():
    calls = []

    def post(url, json=None, timeout=None):
        calls.append(json)
        return FakeResponse({"status": "ok", "defects": 11})

    assert instructor.upload_ground_truth("https://example.test/exec", "tok", post=post) is True
    assert calls[0]["token"] == "tok" and len(calls[0]["defects"]) == 11


def test_resolution_table_lists_missed_defects():
    snippets = load_snippets()
    records = run_matrix(RunContext("G", "mock", "t", lambda r: None), MockClient(snippets), snippets,
                         ("strict",), (False,))
    table = instructor.resolution_table(records)
    bank = table[(table["Snippet"] == "bank_account")].iloc[0]
    assert bank["gefunden"] == "B1"
    assert bank["übersehen"] == "B2, B3, Q1, Q2, Q3"


def test_openrouter_usage():
    def get(url, headers=None, timeout=None):
        assert headers["Authorization"] == "Bearer sk-test"
        return FakeResponse({"data": {"usage": 1.25, "limit": 2.0}})

    assert instructor.openrouter_usage("sk-test", get=get) == {"usage": 1.25, "limit": 2.0}
