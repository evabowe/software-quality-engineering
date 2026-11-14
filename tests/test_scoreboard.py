"""Tests für den Scoreboard-Client und die CSV-Sicherung."""

import csv
import threading

import pytest
import requests

from judge_lab.scoreboard import RECORD_FIELDS, Scoreboard

URL = "https://example.test/exec"


class FakeResponse:
    def __init__(self, status=200, payload=None):
        self.status_code = status
        self._payload = payload if payload is not None else {"status": "ok"}

    def json(self):
        return self._payload


class FakePost:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, url, json=None, timeout=None):
        self.calls.append({"url": url, "json": json, "timeout": timeout})
        response = self.responses.pop(0) if self.responses else FakeResponse()
        if isinstance(response, Exception):
            raise response
        return response


def record(**overrides):
    return {"gruppe": "Gruppe 1", "runde": 2, "snippet": "bank_account", "judge_score": 1, **overrides}


def rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.reader(handle))


def test_record_fields_are_the_contract():
    assert RECORD_FIELDS == ("timestamp", "run_id", "gruppe", "runde", "snippet", "komplexitaet", "modell",
                             "prompt", "code_score", "judge_score", "judge_max", "gefunden", "fehler_gesamt",
                             "fehlalarme", "einreichung")


def test_submit_posts_records_in_one_request(tmp_path):
    post = FakePost(FakeResponse())
    board = Scoreboard(URL, "tok", tmp_path / "backup.csv", post=post)
    assert board.submit([record(), record(snippet="qb_bitcount")]) is True
    assert len(post.calls) == 1
    assert post.calls[0]["json"] == {"token": "tok", "records": [record(), record(snippet="qb_bitcount")]}
    assert post.calls[0]["timeout"] == 10
    assert not (tmp_path / "backup.csv").exists()


def test_retries_then_succeeds(tmp_path):
    post = FakePost(requests.ConnectionError("down"), FakeResponse(503), FakeResponse())
    board = Scoreboard(URL, "tok", tmp_path / "backup.csv", post=post)
    assert board.submit([record()]) is True
    assert len(post.calls) == 3


def test_failure_writes_all_rows_to_csv(tmp_path):
    post = FakePost(*[requests.Timeout("slow")] * 3)
    backup = tmp_path / "backup.csv"
    board = Scoreboard(URL, "tok", backup, post=post)
    assert board.submit([record(judge_score=i) for i in range(5)]) is False
    content = rows(backup)
    assert content[0] == list(RECORD_FIELDS)
    assert len(content) == 6
    assert [r[RECORD_FIELDS.index("judge_score")] for r in content[1:]] == ["0", "1", "2", "3", "4"]


def test_second_failure_appends_without_second_header(tmp_path):
    backup = tmp_path / "backup.csv"
    board = Scoreboard("", "", backup)
    board.submit([record()])
    board.submit([record()])
    assert len(rows(backup)) == 3


def test_rejected_token_counts_as_failure(tmp_path):
    post = FakePost(*[FakeResponse(200, {"status": "error", "message": "bad token"})] * 3)
    board = Scoreboard(URL, "wrong", tmp_path / "backup.csv", post=post)
    assert board.submit([record()]) is False
    assert (tmp_path / "backup.csv").exists()


def test_empty_url_goes_to_csv(tmp_path):
    post = FakePost()
    board = Scoreboard("", "", tmp_path / "backup.csv", post=post)
    assert board.submit([record()]) is False
    assert post.calls == []
    assert len(rows(tmp_path / "backup.csv")) == 2


def test_concurrent_submits_keep_rows_intact(tmp_path):
    backup = tmp_path / "backup.csv"
    board = Scoreboard("", "", backup)
    threads = [threading.Thread(target=board.submit, args=([record(judge_score=i, prompt="x" * 2000)],))
               for i in range(20)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    content = rows(backup)
    assert len(content) == 21
    assert sorted(int(r[RECORD_FIELDS.index("judge_score")]) for r in content[1:]) == list(range(20))


def test_replay_sends_backup_in_one_request_and_clears_it(tmp_path):
    backup = tmp_path / "backup.csv"
    Scoreboard("", "", backup).submit([record(judge_score=1), record(judge_score=2)])
    post = FakePost(FakeResponse())
    board = Scoreboard(URL, "tok", backup, post=post)
    assert board.replay_backup() == 2
    assert len(post.calls) == 1
    assert [r["judge_score"] for r in post.calls[0]["json"]["records"]] == ["1", "2"]
    assert not backup.exists()


def test_replay_keeps_backup_on_failure(tmp_path):
    backup = tmp_path / "backup.csv"
    Scoreboard("", "", backup).submit([record()])
    board = Scoreboard(URL, "tok", backup, post=FakePost(*[requests.ConnectionError("down")] * 3))
    assert board.replay_backup() == 0
    assert len(rows(backup)) == 2


def test_replay_without_backup_does_nothing(tmp_path):
    assert Scoreboard(URL, "tok", tmp_path / "none.csv", post=FakePost()).replay_backup() == 0


def test_unknown_field_rejected(tmp_path):
    with pytest.raises(ValueError, match="unbekannt"):
        Scoreboard("", "", tmp_path / "backup.csv").submit([record(colour="blue")])


def test_default_backup_is_in_working_directory(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert Scoreboard("", "").backup_path == tmp_path / "scoreboard_backup.csv"
