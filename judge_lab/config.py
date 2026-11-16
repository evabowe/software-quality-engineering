"""Zentrale Konfiguration: Pfade, Modell, Bewertungsparameter und Scoreboard."""

from pathlib import Path

# Das Paket liegt flach im Repository; die Datenordner liegen daneben.
REPO_ROOT = Path(__file__).resolve().parent.parent
SNIPPETS_DIR = REPO_ROOT / "snippets"
PROMPTS_DIR = REPO_ROOT / "prompts"

# --- Modell -------------------------------------------------------------------

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
# Standardmodell (am 14.11.2026 in openrouter.ai/api/v1/models vorhanden). Jede andere
# OpenRouter-ID funktioniert ebenso; "mock" nutzt den Mock-Client ohne Kosten.
#DEFAULT_MODEL = "openai/gpt-4.1-nano"
DEFAULT_MODEL = "google/gemini-3.1-flash-lite"
# --- Judge ------------------------------------------------------------------

# Gewichte der Bewertungsdimensionen (prompts/scale_iso25010.md); Summe 1.0
WEIGHTS = {"functional_correctness": 0.40, "reliability": 0.20, "maintainability": 0.25, "readability": 0.15}

# Judge-Score: Punkte pro echtem Defekt bzw. Fehlalarm
POINTS = {"tp": 2, "fp_bug": -1}

TEMPERATURE = 0.0  # Reproduzierbarkeit (Reasoning-Modelle ignorieren den Wert)
# Reasoning-Modelle wie GPT-6 Luna zählen ihre Denk-Tokens mit (gemessen bis ~1900); die Antwort braucht
# bis ~2500 mehr. Kosten bei 16000: ≤ 0,01 $ pro Aufruf.
MAX_TOKENS = 16000
TIMEOUT_S = 90  # Sekunden pro LLM-Aufruf
MAX_RETRIES = 3  # bei 429/5xx/Timeout, exponentieller Backoff im openai-SDK
CONCURRENCY = 6  # parallele Aufrufe in bewerte_alle

# --- Scoreboard -------------------------------------------------------------

# Nach dem Deployment der Apps-Script-Web-App eintragen (docs/DASHBOARD_TEST.md).
# Leere URL: Ergebnisse landen nur in der lokalen CSV-Sicherung.
SCOREBOARD_URL = "https://script.google.com/macros/s/AKfycbwXy2n88oda5nLpq1J2SVzG5J3D5SX0wPi82gtKlSvz2jdw5p1dIYabfz0ef8Ks9d19Zw/exec"
SCOREBOARD_TOKEN = "3551d940879490ee5fc93673928866b2"
SCOREBOARD_TIMEOUT = 10  # Sekunden
SCOREBOARD_RETRIES = 2
