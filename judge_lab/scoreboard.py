"""Übertragung der Läufe an das Scoreboard (Google Apps Script) mit lokaler CSV-Sicherung.

Jeder Lauf wird sofort gesendet (Live-Effekt am Beamer). Ist das Scoreboard
nicht erreichbar, landet der Lauf in einer CSV-Datei und geht nicht verloren;
``replay_backup`` sendet ihn später nach.
"""

from __future__ import annotations

import csv
import threading
from pathlib import Path

import requests

from judge_lab.config import SCOREBOARD_RETRIES, SCOREBOARD_TIMEOUT

# Eine Zeile pro LLM-Lauf (Konzept 8.8). Dieselbe Reihenfolge steht als FIELDS in scoreboard/Code.gs.
RECORD_FIELDS = (
    "timestamp",
    "session_id",
    "group",
    "phase",  # prognosis | a1 | a2_probe | a2_submit | reference
    "model_key",
    "model_id",
    "attitude",
    "snippet_id",
    "complexity_level",
    "with_tests",
    "prompt_hash",
    "prompt_text",  # nur bei a2_submit
    "submission_no",
    "tp",
    "fp",
    "neutral",
    "n_defects",
    "recall",
    "precision",
    "weighted_score",
    "llm_overall_score",
    "scores_json",
    "found_defect_ids",
    "findings_json",
    "parse_ok",
    "error",
    "latency_s",
    "tokens_in",
    "tokens_out",
    "prediction_best_model",
    "prediction_strict_vs_lenient",
    "notebook_version",
)


def default_backup_path() -> Path:
    """In Colab unter /content, sonst im aktuellen Verzeichnis."""
    colab = Path("/content")
    return (colab if colab.is_dir() else Path.cwd()) / "scoreboard_backup.csv"


class Scoreboard:
    def __init__(self, url: str, token: str, backup_path: Path | None = None, *, post=requests.post):
        self.url = url
        self.token = token
        self.backup_path = Path(backup_path) if backup_path else default_backup_path()
        self._post = post
        self._lock = threading.Lock()

    def submit(self, record: dict) -> bool:
        """True, wenn das Scoreboard den Lauf angenommen hat; sonst wird er in der CSV gesichert."""
        unknown = set(record) - set(RECORD_FIELDS)
        if unknown:
            raise ValueError(f"Datensatz enthält unbekannte Felder: {sorted(unknown)}")
        if self._send(record):
            return True
        self._append_backup(record)
        return False

    def replay_backup(self) -> int:
        """Sendet gesicherte Läufe erneut; erfolgreich gesendete verschwinden aus der CSV."""
        with self._lock:
            if not self.backup_path.exists():
                return 0
            with self.backup_path.open(newline="", encoding="utf-8") as handle:
                pending = list(csv.DictReader(handle))
            failed = [row for row in pending if not self._send(row)]
            self._write_rows(failed, mode="w")
        return len(pending) - len(failed)

    def _send(self, record: dict) -> bool:
        if not self.url:
            return False
        for _ in range(1 + SCOREBOARD_RETRIES):
            try:
                response = self._post(
                    self.url, json={"token": self.token, "record": record}, timeout=SCOREBOARD_TIMEOUT
                )
                if response.status_code == 200 and response.json().get("status") == "ok":
                    return True
            except (requests.RequestException, ValueError):
                pass
        return False

    def _append_backup(self, record: dict) -> None:
        with self._lock:
            self._write_rows([record], mode="a")

    def _write_rows(self, records: list[dict], mode: str) -> None:
        write_header = mode == "w" or not self.backup_path.exists()
        with self.backup_path.open(mode, newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=RECORD_FIELDS, restval="")
            if write_header:
                writer.writeheader()
            writer.writerows(records)
