"""Tests für den Gruppencode: Normalisierung, Antworten des Code-Servers, Fehlermeldungen."""

import pytest
import requests

from judge_lab import join
from judge_lab.llm import ConfigError


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=None):
        self.status_code = status_code
        self._payload = payload
        self._text = text

    def json(self):
        if self._payload is None:
            raise ValueError("kein JSON")
        return self._payload


def fake_get(response=None, exc=None, calls=None):
    def get(url, params=None, timeout=None):
        if calls is not None:
            calls.append((url, params, timeout))
        if exc:
            raise exc
        return response

    return get


@pytest.mark.parametrize("raw, expected", [("K7Q2", "K7Q2"), ("k7q2", "K7Q2"), (" k7 q2\n", "K7Q2"),
                                           ("\tK 7 Q 2 ", "K7Q2")])
def test_normalize_code(raw, expected):
    assert join.normalize_code(raw) == expected


def test_join_returns_group_and_key():
    calls = []
    get = fake_get(FakeResponse(payload={"status": "ok", "group": "Gruppe 2", "key": "sk-test"}), calls=calls)
    assert join.join(" k7q2 ", url="https://x/exec", token="t", get=get) == ("Gruppe 2", "sk-test")
    _, params, _ = calls[0]
    assert params == {"action": "join", "code": "K7Q2", "token": "t"}


def test_unknown_code_gives_german_message():
    get = fake_get(FakeResponse(payload={"status": "error", "message": "Code unbekannt"}))
    with pytest.raises(ConfigError, match="Code unbekannt") as info:
        join.join("ZZZZ", url="https://x/exec", token="t", get=get)
    assert not isinstance(info.value, join.ServerUnreachable)


def test_empty_code_is_not_sent():
    calls = []
    with pytest.raises(ConfigError, match="Gruppencode"):
        join.join("  ", url="https://x/exec", token="t", get=fake_get(calls=calls))
    assert calls == []


@pytest.mark.parametrize("get", [
    fake_get(exc=requests.ConnectionError("offline")),
    fake_get(exc=requests.Timeout("langsam")),
    fake_get(FakeResponse(status_code=500, payload={})),
    fake_get(FakeResponse(payload=None)),  # HTML-Fehlerseite statt JSON
])
def test_unreachable_server(get):
    with pytest.raises(join.ServerUnreachable, match="Notfall-Folie"):
        join.join("K7Q2", url="https://x/exec", token="t", get=get)


def test_no_url_counts_as_unreachable():
    with pytest.raises(join.ServerUnreachable):
        join.join("K7Q2", url="", token="t", get=fake_get(FakeResponse(payload={})))


def test_join_accepts_any_group_name():
    get = fake_get(FakeResponse(payload={"status": "ok", "group": "Team Rot", "key": "sk-test"}))
    assert join.join("K7Q2", url="https://x/exec", token="t", get=get) == ("Team Rot", "sk-test")
