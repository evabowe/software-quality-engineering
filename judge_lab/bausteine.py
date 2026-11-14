"""Die vier Bausteine für das Notebook: verbinde, bewerte, bewerte_alle, sende.

Alles andere (OpenRouter, Prompt-Aufbau, Parsing, Abgleich mit der Ground Truth,
Google Sheet) läuft im Hintergrund. Keine Funktion wirft bei erwartbaren Fehlern:
Sie gibt eine kurze deutsche Meldung aus und markiert das Ergebnis mit ``fehler``.
"""

from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

from judge_lab import join as _join_module
from judge_lab.config import CONCURRENCY, DEFAULT_MODEL, SCOREBOARD_TOKEN, SCOREBOARD_URL
from judge_lab.llm import ConfigError, make_client
from judge_lab.matching import match_findings
from judge_lab.prompts import build_prompt
from judge_lab.runner import judge
from judge_lab.scoring import challenge_points, weighted_score
from judge_lab.snippets import Snippet, load_snippets

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
    if verdict is None:
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
