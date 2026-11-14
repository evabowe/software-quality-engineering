"""Die vier Bausteine für das Notebook: verbinde, bewerte, bewerte_alle, sende.

Alles andere (OpenRouter, Prompt-Aufbau, Parsing, Abgleich mit der Ground Truth,
Google Sheet) läuft im Hintergrund. Keine Funktion wirft bei erwartbaren Fehlern:
Sie gibt eine kurze deutsche Meldung aus und markiert das Ergebnis mit ``fehler``.
"""

from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from functools import lru_cache

from judge_lab import join as _join_module
from judge_lab.config import CONCURRENCY, DEFAULT_MODEL, SCOREBOARD_TOKEN, SCOREBOARD_URL
from judge_lab.llm import ConfigError, make_client
from judge_lab.matching import match_findings
from judge_lab.prompts import build_prompt
from judge_lab.runner import judge
from judge_lab.scoreboard import RECORD_FIELDS, Scoreboard
from judge_lab.scoring import challenge_points, weighted_score
from judge_lab.snippets import Snippet, load_snippets

RUNDEN = {1: "Frei ausprobieren", 2: "Rollen vergleichen", 3: "Komplexität vergleichen", 4: "AI Challenge"}

# Gruppe und Key nach verbinde(); gilt für alle weiteren Aufrufe im Notebook.
_ZUSTAND = {"gruppe": "", "key": ""}
_join = _join_module.join

UNLESBAR = "Die Antwort des Modells war nicht lesbar – bitte noch einmal versuchen."


# --- verbinde -----------------------------------------------------------------


def verbinde(code: str = "", *, key: str = "", gruppe: str = "") -> None:
    """Code von der Folie eingeben; Notfall ohne Code-Server: ``verbinde(key="…", gruppe="…")``."""
    if not code and (key or gruppe):
        if not (key and gruppe):
            print('❌ Für den Notfall-Weg bitte beides angeben: verbinde(key="…", gruppe="…")')
            return
        _ZUSTAND.update(gruppe=gruppe.strip(), key=key.strip())
        print(f"✅ Verbunden als {_ZUSTAND['gruppe']} (Notfall-Weg).")
        return
    try:
        gruppe_vom_server, key_vom_server = _join(code, url=SCOREBOARD_URL, token=SCOREBOARD_TOKEN)
    except ConfigError as exc:
        print(f"❌ {exc}")
        return
    _ZUSTAND.update(gruppe=gruppe_vom_server, key=key_vom_server)
    print(f"✅ Verbunden als {gruppe_vom_server}.")


# --- bewerte ------------------------------------------------------------------


def _ergebnis(prompt: str, snippet_id: str, komplexitaet: str, modell: str, einreichung: str) -> dict:
    return {
        "code_score": None,
        "judge_score": None,
        "snippet": snippet_id,
        "komplexitaet": komplexitaet,
        "modell": modell,
        "prompt": prompt,
        "gruppe": _ZUSTAND["gruppe"],
        "einreichung": einreichung,
        "fehler": None,
    }


def _fehlschlag(ergebnis: dict, fehler: str, *, melden: bool = True) -> dict:
    ergebnis["fehler"] = fehler
    if melden:
        print(f"⚠️ {ergebnis['snippet']}: {fehler}")
    return ergebnis


def _kurzgrund(error: str) -> str:
    grund = error.removeprefix("LLM-Aufruf fehlgeschlagen: ").strip()
    return grund if len(grund) <= 120 else grund[:117] + "…"


def _bewerte_snippet(client, prompt: str, snippet: Snippet, modell: str, einreichung: str) -> dict:
    ergebnis = _ergebnis(prompt, snippet.id, snippet.level or "", modell, einreichung)
    try:
        messages = build_prompt(snippet, with_tests=False, custom_block=prompt)
        verdict, result, _ = judge(client, messages, snippet.line_count)
    except Exception as exc:  # noqa: BLE001 – Studierende sollen nie einen Traceback sehen
        return _fehlschlag(ergebnis, f"Unerwarteter Fehler ({type(exc).__name__}: {exc}).")
    if result.error:
        return _fehlschlag(
            ergebnis,
            f"Das Modell war nicht erreichbar oder hat abgelehnt ({_kurzgrund(result.error)}). "
            "Key, Guthaben oder Modellname prüfen.",
        )
    if verdict is None or not (verdict.findings or verdict.scores):
        # Abgeschnittene Antwort oder Ablehnung: kein Urteil – nicht als „0 Fehler gefunden“ werten.
        return _fehlschlag(ergebnis, UNLESBAR)
    ergebnis["code_score"] = weighted_score(verdict.scores)
    ergebnis["judge_score"] = challenge_points([match_findings(verdict.findings, snippet.defects)])
    return ergebnis


def _client_oder_fehler(modell: str):
    try:
        return make_client(modell, _ZUSTAND["key"]), None
    except ConfigError as exc:
        return None, str(exc)


def bewerte(prompt: str, snippet: str = "bank_account", modell: str = DEFAULT_MODEL) -> dict:
    """Lässt das Modell ein Snippet mit eurem Prompt begutachten; liefert Code-Score und Judge-Score."""
    einreichung = uuid.uuid4().hex
    snippets = {s.id: s for s in load_snippets()}
    ziel = snippets.get(snippet)
    ergebnis = _ergebnis(prompt, snippet, (ziel.level or "") if ziel else "", modell, einreichung)
    if not (prompt or "").strip():
        return _fehlschlag(ergebnis, "Der Prompt ist leer.")
    if ziel is None:
        return _fehlschlag(ergebnis, f"Unbekanntes Snippet. Möglich sind: {', '.join(sorted(snippets))}.")
    client, fehler = _client_oder_fehler(modell)
    if fehler:
        return _fehlschlag(ergebnis, fehler)
    return _bewerte_snippet(client, prompt, ziel, modell, einreichung)


def bewerte_alle(prompt: str, modell: str = DEFAULT_MODEL) -> list[dict]:
    """Bewertet die fünf Snippets L1–L5 parallel (Runde 3 und 4); eine gemeinsame Einreichung."""
    einreichung = uuid.uuid4().hex
    ziele = [s for s in load_snippets() if s.level]
    fehler = "Der Prompt ist leer." if not (prompt or "").strip() else None
    client = None
    if not fehler:
        client, fehler = _client_oder_fehler(modell)
    if fehler:
        print(f"⚠️ {fehler}")
        return [_fehlschlag(_ergebnis(prompt, s.id, s.level, modell, einreichung), fehler, melden=False)
                for s in ziele]

    ergebnisse: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        futures = [pool.submit(_bewerte_snippet, client, prompt, s, modell, einreichung) for s in ziele]
        for fertig, future in enumerate(as_completed(futures), start=1):
            ergebnis = future.result()
            ergebnisse[ergebnis["snippet"]] = ergebnis
            print(f"{fertig}/{len(ziele)} fertig", end="\r")
    print()
    return [ergebnisse[s.id] for s in ziele]


# --- sende --------------------------------------------------------------------


@lru_cache(maxsize=1)
def _scoreboard() -> Scoreboard:
    return Scoreboard(SCOREBOARD_URL, SCOREBOARD_TOKEN)


def _zeile(ergebnis: dict, runde: int) -> dict:
    zeile = {feld: ergebnis.get(feld, "") for feld in RECORD_FIELDS}
    zeile.update(
        timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        # Gleiches Ergebnis in gleicher Runde → gleiche run_id; das Dashboard zählt es dann einmal.
        run_id=uuid.uuid5(uuid.NAMESPACE_URL, f"{ergebnis.get('einreichung')}:{ergebnis.get('snippet')}:{runde}").hex,
        runde=runde,
    )
    return {feld: ("" if wert is None else wert) for feld, wert in zeile.items()}


def sende(ergebnis: dict | list[dict], runde: int) -> bool:
    """Schickt das Ergebnis von bewerte (Runde 1–2) bzw. bewerte_alle (Runde 3–4) ans Dashboard."""
    if type(runde) is not int or runde not in RUNDEN:
        print("❌ Bitte eine Runde von 1–4 angeben, z. B. sende(ergebnis, runde=2).")
        return False
    liste = isinstance(ergebnis, list)
    if runde in (1, 2) and liste:
        print(f"❌ Für Runde {runde} bitte das Ergebnis von bewerte(…) senden, nicht die Liste von bewerte_alle.")
        return False
    if runde in (3, 4) and not liste:
        print(f"❌ Für Runde {runde} bitte das Ergebnis von bewerte_alle(…) senden.")
        return False
    ergebnisse = ergebnis if liste else [ergebnis]
    if not ergebnisse or not all(isinstance(e, dict) for e in ergebnisse):
        print("❌ Bitte das Ergebnis von bewerte(…) bzw. bewerte_alle(…) senden.")
        return False
    if any(e.get("modell") == "mock" for e in ergebnisse):
        print("ℹ️ Mock-Ergebnisse gehen nicht ans Dashboard.")
        return False
    fehlerhaft = [e for e in ergebnisse if e.get("fehler")]
    if fehlerhaft:
        namen = ", ".join(e.get("snippet", "?") for e in fehlerhaft)
        print(f"⚠️ Nicht gesendet, weil die Bewertung fehlgeschlagen ist: {namen}")
    zeilen = [_zeile(e, runde) for e in ergebnisse if not e.get("fehler")]
    if not zeilen:
        print("❌ Nichts zu senden.")
        return False

    board = _scoreboard()
    board.replay_backup()
    if board.submit(zeilen):
        print(f"✅ {len(zeilen)} Ergebnis(se) gesendet – das Dashboard zeigt es in ein paar Sekunden.")
        return True
    if board.last_error:
        print(f"⚠️ Das Dashboard hat abgelehnt: {board.last_error} – lokal gesichert.")
    else:
        print("⚠️ Dashboard nicht erreichbar – lokal gesichert, wird beim nächsten Senden nachgeholt.")
    return False
