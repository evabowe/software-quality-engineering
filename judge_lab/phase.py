"""Phasenfreigabe: Die Lehrenden schalten die Reiter vom Dashboard aus frei.

Das Notebook fragt alle ``POLL_S`` Sekunden ``?format=phase`` ab. Antwortet der
Endpunkt ``OFFLINE_AFTER``-mal hintereinander nicht, gilt die Freigabe als offline
und alle Reiter werden geöffnet – die Gruppen folgen dann der Ansage vorne.
"""

from __future__ import annotations

from collections.abc import Callable

import requests

from judge_lab.config import SCOREBOARD_TIMEOUT

POLL_S = 10
OFFLINE_AFTER = 3
MAX_PHASE = 5
OFFLINE_MESSAGE = "Freigabe offline – folgt einfach der Ansage vorne."


class PhaseUnavailable(RuntimeError):
    """Keine gültige Antwort vom Phasen-Endpunkt."""


def fetch_phase(url: str, get=requests.get) -> int:
    try:
        response = get(url, params={"format": "phase"}, timeout=SCOREBOARD_TIMEOUT)
        value = response.json().get("phase") if response.status_code == 200 else None
    except (requests.RequestException, ValueError, AttributeError) as exc:
        raise PhaseUnavailable(str(exc)) from exc
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= MAX_PHASE:
        raise PhaseUnavailable(f"unerwartete Antwort: {value!r}")
    return value


def _no_url() -> int:
    raise PhaseUnavailable("keine Scoreboard-URL")


class PhaseGate:
    """Entscheidet je Abfrage, bis zu welchem Reiter entsperrt wird (None = nichts ändern)."""

    def __init__(self, fetch: Callable[[], int], *, offline_after: int = OFFLINE_AFTER):
        self._fetch = fetch
        self._offline_after = offline_after
        self.failures = 0
        self.offline = False

    @classmethod
    def for_url(cls, url: str, get=requests.get) -> PhaseGate:
        if not url:
            # Ohne Scoreboard gibt es keine Freigabe: sofort alles öffnen.
            return cls(_no_url, offline_after=1)
        return cls(lambda: fetch_phase(url, get=get))

    def tick(self) -> int | None:
        try:
            phase = self._fetch()
        except PhaseUnavailable:
            self.failures += 1
            if self.failures >= self._offline_after:
                self.offline = True
                return MAX_PHASE
            return None
        self.failures, self.offline = 0, False
        return phase
