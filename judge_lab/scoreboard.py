"""Übertragung der Ergebnisse an das Scoreboard (Google Apps Script) mit lokaler CSV-Sicherung.

``sende`` übergibt alle Zeilen eines Aufrufs in einem Request. Ist das Scoreboard
nicht erreichbar, landen sie in einer CSV-Datei und gehen nicht verloren;
``replay_backup`` sendet sie später nach.
"""

from __future__ import annotations

import csv
import threading
from pathlib import Path

import requests

from judge_lab.config import SCOREBOARD_RETRIES, SCOREBOARD_TIMEOUT

# Eine Zeile pro bewertetem Snippet. Dieselbe Reihenfolge steht als FIELDS in scoreboard/Code.gs
# (dort zusätzlich session_id, das Apps Script beim Empfang setzt).
RECORD_FIELDS = (
    "timestamp",
    "run_id",  # eindeutig je Zeile; das Dashboard entfernt doppelt gesendete Zeilen
    "gruppe",
    "runde",  # 1 frei · 2 Rollen · 3 Komplexität · 4 AI Challenge
    "snippet",
    "komplexitaet",  # L1–L5 oder leer
    "modell",
    "prompt",
    "code_score",
    "judge_score",
    "einreichung",  # gleiche ID für alle Zeilen eines bewerte_alle-Aufrufs
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

    def submit(self, records: list[dict]) -> bool:
        """True, wenn das Scoreboard die Zeilen angenommen hat; sonst werden alle in der CSV gesichert."""
        for record in records:
            unknown = set(record) - set(RECORD_FIELDS)
            if unknown:
                raise ValueError(f"Datensatz enthält unbekannte Felder: {sorted(unknown)}")
        if self._send(records):
            return True
        with self._lock:
            self._write_rows(records, mode="a")
        return False

    def replay_backup(self) -> int:
        """Sendet alle gesicherten Zeilen in einem Request; bei Erfolg verschwindet die CSV."""
        with self._lock:
            if not self.backup_path.exists():
                return 0
            with self.backup_path.open(newline="", encoding="utf-8") as handle:
                pending = list(csv.DictReader(handle))
            if not pending:
                self.backup_path.unlink()
                return 0
            if not self._send(pending):
                return 0
            self.backup_path.unlink()
        return len(pending)

    def _send(self, records: list[dict]) -> bool:
        if not self.url:
            return False
        for _ in range(1 + SCOREBOARD_RETRIES):
            try:
                response = self._post(
                    self.url, json={"token": self.token, "records": records}, timeout=SCOREBOARD_TIMEOUT
                )
                if response.status_code == 200 and response.json().get("status") == "ok":
                    return True
            except (requests.RequestException, ValueError):
                pass
        return False

    def _write_rows(self, records: list[dict], mode: str) -> None:
        write_header = mode == "w" or not self.backup_path.exists()
        with self.backup_path.open(mode, newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=RECORD_FIELDS, restval="")
            if write_header:
                writer.writeheader()
            writer.writerows(records)
