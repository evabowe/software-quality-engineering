"""Gruppencode: Die Studierenden tippen nur einen kurzen Code von der Folie ab.

Der Code-Server (``?action=join`` der Scoreboard-Web-App) liest den privaten Tab
``keys`` und gibt Gruppe und OpenRouter-Key zurück. Ist er nicht erreichbar,
entsteht ``ServerUnreachable``; die Oberfläche öffnet dann den Notfall-Weg
(Gruppe und Key von Hand).
"""

from __future__ import annotations

import re

import requests

from judge_lab.config import GROUPS, SCOREBOARD_TIMEOUT
from judge_lab.llm import ConfigError


class ServerUnreachable(ConfigError):
    """Der Code-Server antwortet nicht (Netz, URL, Fehlerseite)."""


UNREACHABLE = "Code-Server nicht erreichbar – bitte Gruppe und Key von der Notfall-Folie eintragen (unter „Erweitert“)."


def normalize_code(text: str) -> str:
    """Groß/klein egal, Leerzeichen und Zeilenumbrüche werden entfernt."""
    return re.sub(r"\s+", "", text or "").upper()


def join(code: str, *, url: str, token: str, session_id: str, get=requests.get) -> tuple[str, str]:
    """(Gruppe, API-Key) zum Code. Wirft ConfigError mit deutscher Meldung."""
    code = normalize_code(code)
    if not code:
        raise ConfigError("Bitte den Gruppencode von der Folie eingeben.")
    if not url:
        raise ServerUnreachable(UNREACHABLE)
    params = {"action": "join", "code": code, "token": token, "session": session_id}
    try:
        response = get(url, params=params, timeout=SCOREBOARD_TIMEOUT)
        payload = response.json() if response.status_code == 200 else None
    except (requests.RequestException, ValueError):
        payload = None
    if not isinstance(payload, dict) or "status" not in payload:
        raise ServerUnreachable(UNREACHABLE)
    if payload["status"] != "ok":
        raise ConfigError(f"{payload.get('message') or 'Code unbekannt'} – bitte den Code noch einmal von der Folie abtippen.")
    group = payload.get("group", "")
    if group not in GROUPS:
        raise ConfigError(f"Der Code gehört zu {group!r}, diese Gruppe kennt das Notebook nicht. Bitte Bescheid geben.")
    return group, payload.get("key", "")
