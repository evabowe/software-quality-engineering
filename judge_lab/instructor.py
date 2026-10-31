"""Hilfsfunktionen für das Instructor-Notebook: Vorab-Läufe, Ground Truth, Auflösung, Kosten.

Anders als die Studierenden-UI zeigen diese Funktionen die Ground Truth.
"""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd
import requests

from judge_lab.config import SCOREBOARD_TIMEOUT
from judge_lab.llm import make_client
from judge_lab.runner import RunContext, assignment1_variants, run_matrix
from judge_lab.scoreboard import Scoreboard
from judge_lab.snippets import load_snippets

OPENROUTER_KEY_URL = "https://openrouter.ai/api/v1/key"


def precompute(model_keys: Sequence[str], api_key: str, board: Scoreboard, session_id: str = "precomputed",
               on_progress=None) -> list[dict]:
    """Auftrag 1 für mehrere Modelle als Backup-Daten (Dashboard-Schalter „Vorab-Daten“)."""
    snippets = load_snippets()
    records = []
    for key in model_keys:
        attitudes, variants = assignment1_variants(key)
        ctx = RunContext(group="Vorab", model_key=key, session_id=session_id, sink=board.submit)
        records += run_matrix(ctx, make_client(key, api_key), snippets, attitudes, variants, on_progress=on_progress)
    return records


def ground_truth_rows() -> list[dict]:
    rows = []
    for snippet in load_snippets():
        for d in snippet.defects:
            lines = str(d.lines[0]) if d.lines[0] == d.lines[1] else f"{d.lines[0]}–{d.lines[1]}"
            rows.append({"snippet_id": snippet.id, "defect_id": d.id, "kind": d.kind, "lines": lines,
                         "description": d.description})
    return rows


def upload_ground_truth(url: str, token: str, post=requests.post) -> bool:
    """Füllt den Tab „defects“ des Scoreboards (für RQ1-Matrix und Auflösung)."""
    response = post(url, json={"token": token, "defects": ground_truth_rows()}, timeout=SCOREBOARD_TIMEOUT)
    return response.status_code == 200 and response.json().get("status") == "ok"


def resolution_table(records: list[dict]) -> pd.DataFrame:
    """Je Lauf: welche Defekte gefunden, welche übersehen wurden."""
    defects = {s.id: [d.id for d in s.defects] for s in load_snippets()}
    rows = []
    for r in records:
        found = [d for d in str(r["found_defect_ids"]).split(",") if d]
        rows.append({
            "Snippet": r["snippet_id"],
            "Modell": r["model_key"],
            "Haltung": r["attitude"],
            "Tests": "mit" if str(r["with_tests"]).lower() == "true" else "ohne",
            "gefunden": ", ".join(found),
            "übersehen": ", ".join(d for d in defects[r["snippet_id"]] if d not in found),
            "Fehlalarme": r["fp"],
        })
    return pd.DataFrame(rows)


def openrouter_usage(api_key: str, get=requests.get) -> dict:
    """Verbrauch und Limit eines OpenRouter-Keys (in US-Dollar)."""
    response = get(OPENROUTER_KEY_URL, headers={"Authorization": f"Bearer {api_key}"}, timeout=SCOREBOARD_TIMEOUT)
    data = response.json().get("data", {})
    return {"usage": data.get("usage"), "limit": data.get("limit")}
