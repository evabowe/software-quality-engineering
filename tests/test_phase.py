"""Tests für die Phasenfreigabe: Abfrage, Entsperren, Offline-Fallback."""

import pytest
import requests

from judge_lab import app, phase, ui
from judge_lab.scoreboard import Scoreboard


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code, self._payload = status_code, payload

    def json(self):
        if self._payload is None:
            raise ValueError("kein JSON")
        return self._payload


def test_fetch_phase_reads_number():
    calls = []

    def get(url, params=None, timeout=None):
        calls.append(params)
        return FakeResponse(payload={"phase": 2})

    assert phase.fetch_phase("https://x/exec", get=get) == 2
    assert calls == [{"format": "phase"}]


@pytest.mark.parametrize("response", [FakeResponse(500, {}), FakeResponse(payload=None),
                                      FakeResponse(payload={"phase": "zwei"}), FakeResponse(payload={"phase": 9}),
                                      FakeResponse(payload={})])
def test_fetch_phase_rejects_bad_answers(response):
    with pytest.raises(phase.PhaseUnavailable):
        phase.fetch_phase("https://x/exec", get=lambda *a, **k: response)


def test_fetch_phase_network_error():
    def get(*a, **k):
        raise requests.ConnectionError("offline")

    with pytest.raises(phase.PhaseUnavailable):
        phase.fetch_phase("https://x/exec", get=get)


def scripted(*answers):
    answers = list(answers)

    def fetch():
        answer = answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    return fetch


def test_gate_follows_phase():
    gate = phase.PhaseGate(scripted(0, 1, 3))
    assert [gate.tick() for _ in range(3)] == [0, 1, 3]
    assert not gate.offline


def test_gate_unlocks_everything_after_three_failures():
    down = phase.PhaseUnavailable("x")
    gate = phase.PhaseGate(scripted(1, down, down, down))
    assert gate.tick() == 1
    assert gate.tick() is None and gate.tick() is None and not gate.offline
    assert gate.tick() == app.LAST_PHASE and gate.offline


def test_single_failures_do_not_trigger_fallback():
    down = phase.PhaseUnavailable("x")
    gate = phase.PhaseGate(scripted(down, down, 2, down, down, 2))
    results = [gate.tick() for _ in range(6)]
    assert results == [None, None, 2, None, None, 2] and not gate.offline


def test_gate_recovers_from_offline():
    down = phase.PhaseUnavailable("x")
    gate = phase.PhaseGate(scripted(down, down, down, 2))
    for _ in range(3):
        gate.tick()
    assert gate.offline
    assert gate.tick() == 2 and not gate.offline


def test_gate_without_url_is_offline_at_once():
    gate = phase.PhaseGate.for_url("")
    assert gate.tick() == app.LAST_PHASE and gate.offline


@pytest.fixture
def view(tmp_path, monkeypatch):
    monkeypatch.setattr(ui, "SESSION", ui.Session())
    monkeypatch.setattr(ui, "_scoreboard", lambda: Scoreboard("", "", tmp_path / "backup.csv"))
    monkeypatch.setattr(app, "STATE", app.AppState())
    return app.build()


def test_app_starts_locked(view):
    assert app.STATE.phase == 0
    assert app.LOCK_TEXT in view.containers[1].children[0].value


def test_poll_once_unlocks_view(view):
    gate = phase.PhaseGate(scripted(2))
    app.poll_once(gate)
    assert app.STATE.phase == 2 and app.LOCK_TEXT not in str(view.containers[2].children[0])


def test_offline_shows_message_in_status(view):
    down = phase.PhaseUnavailable("x")
    gate = phase.PhaseGate(scripted(down, down, down))
    for _ in range(3):
        app.poll_once(gate)
    assert app.STATE.phase == app.LAST_PHASE
    assert phase.OFFLINE_MESSAGE in view.status.value


def test_poller_starts_only_once(monkeypatch):
    started = []
    monkeypatch.setattr(app, "_POLLER", None)
    monkeypatch.setattr(app.threading, "Thread", lambda **kw: started.append(kw) or type(
        "T", (), {"start": lambda self: None, "is_alive": lambda self: True})())
    app.start_polling(phase.PhaseGate(scripted()))
    app.start_polling(phase.PhaseGate(scripted()))
    assert len(started) == 1
