"""Tests für den Scoreboard-Client und die CSV-Sicherung."""

import csv
import threading

import pytest
import requests

from judge_lab.scoreboard import RECORD_FIELDS, Scoreboard


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
    return {"session_id": "test", "group": "Gruppe 1", "phase": "a1", "tp": 1, **overrides}


def rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.reader(handle))


def test_submit_posts_payload(tmp_path):
    post = FakePost(FakeResponse())
    board = Scoreboard("https://example.test/exec", "tok", tmp_path / "backup.csv", post=post)
    assert board.submit(record()) is True
    assert post.calls[0]["json"] == {"token": "tok", "record": record()}
    assert post.calls[0]["timeout"] == 10
    assert not (tmp_path / "backup.csv").exists()


def test_retries_then_succeeds(tmp_path):
    post = FakePost(requests.ConnectionError("down"), FakeResponse(503), FakeResponse())
    board = Scoreboard("https://example.test/exec", "tok", tmp_path / "backup.csv", post=post)
    assert board.submit(record()) is True
    assert len(post.calls) == 3


def test_failure_writes_csv_once_with_header(tmp_path):
    post = FakePost(*[requests.Timeout("slow")] * 6)
    backup = tmp_path / "backup.csv"
    board = Scoreboard("https://example.test/exec", "tok", backup, post=post)
    assert board.submit(record(tp=1)) is False
    assert board.submit(record(tp=2)) is False
    content = rows(backup)
    assert content[0] == list(RECORD_FIELDS)
    assert len(content) == 3
    assert content[2][RECORD_FIELDS.index("tp")] == "2"


def test_rejected_token_counts_as_failure(tmp_path):
    post = FakePost(*[FakeResponse(200, {"status": "error", "message": "bad token"})] * 3)
    board = Scoreboard("https://example.test/exec", "wrong", tmp_path / "backup.csv", post=post)
    assert board.submit(record()) is False
    assert (tmp_path / "backup.csv").exists()


def test_empty_url_goes_to_csv(tmp_path):
    post = FakePost()
    board = Scoreboard("", "", tmp_path / "backup.csv", post=post)
    assert board.submit(record()) is False
    assert post.calls == []
    assert len(rows(tmp_path / "backup.csv")) == 2


def test_concurrent_submits_keep_rows_intact(tmp_path):
    backup = tmp_path / "backup.csv"
    board = Scoreboard("", "", backup)
    threads = [threading.Thread(target=board.submit, args=(record(tp=i, error="x" * 2000),)) for i in range(20)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    content = rows(backup)
    assert len(content) == 21
    assert sorted(int(r[RECORD_FIELDS.index("tp")]) for r in content[1:]) == list(range(20))


def test_replay_backup(tmp_path):
    backup = tmp_path / "backup.csv"
    Scoreboard("", "", backup).submit(record(tp=1))
    Scoreboard("", "", backup).submit(record(tp=2))

    post = FakePost(FakeResponse(), *[requests.ConnectionError("down")] * 3)
    board = Scoreboard("https://example.test/exec", "tok", backup, post=post)
    assert board.replay_backup() == 1
    remaining = rows(backup)
    assert len(remaining) == 2  # Kopfzeile + der nicht gesendete Lauf
    assert post.calls[0]["json"]["record"]["tp"] == "1"


def test_replay_without_backup_does_nothing(tmp_path):
    assert Scoreboard("https://example.test/exec", "tok", tmp_path / "none.csv", post=FakePost()).replay_backup() == 0


def test_unknown_field_rejected(tmp_path):
    with pytest.raises(ValueError, match="unbekannt"):
        Scoreboard("", "", tmp_path / "backup.csv").submit(record(colour="blue"))
