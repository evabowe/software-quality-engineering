"""Zentrale Konfiguration: Pfade, Modelle, Gruppen und Bewertungsparameter."""

from pathlib import Path

# Das Paket liegt flach im Repository; die Datenordner liegen daneben.
REPO_ROOT = Path(__file__).resolve().parent.parent
SNIPPETS_DIR = REPO_ROOT / "snippets"
PROMPTS_DIR = REPO_ROOT / "prompts"

# --- Modelle und Gruppen ----------------------------------------------------

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OLLAMA_BASE_URL = "http://localhost:11434/v1"

# Modell-IDs: Stand 31.10.2026 (openrouter.ai/api/v1/models).
# Eine Woche vor der Session erneut prüfen und hier fixieren!
# Eine ID, die noch PLACEHOLDER_MARK enthält, wird vom Client abgelehnt.
MODELS = {
    "gemini": {"provider": "openrouter", "id": "google/gemini-3.8-flash", "label": "Gemini (wie im Paper)"},
    "deepseek": {"provider": "openrouter", "id": "deepseek/deepseek-v4.1-flash", "label": "DeepSeek (wie im Paper)"},
    "kimi": {"provider": "openrouter", "id": "moonshotai/kimi-k2.6", "label": "Kimi (wie im Paper)"},
    "local": {"provider": "ollama", "id": "qwen2.5-coder:3b", "label": "Qwen Coder 3B lokal (Colab T4)"},
    # Fallback für Gruppe 4 ohne GPU: kleines Modell über OpenRouter
    "local_fallback": {"provider": "openrouter", "id": "qwen/qwen3-coder-flash", "label": "Qwen Coder klein (OpenRouter)"},
    "reference": {"provider": "openrouter", "id": "qwen/qwen3-coder-next", "label": "Referenz (Qwen3 Coder)"},
    "mock": {"provider": "mock", "id": "mock", "label": "Mock (Probe)"},
}
PLACEHOLDER_MARK = "<"

GROUPS = {
    "Gruppe 1": {"model_key": "gemini"},
    "Gruppe 2": {"model_key": "deepseek"},
    "Gruppe 3": {"model_key": "kimi"},
    "Gruppe 4": {"model_key": "local"},
}

# --- Judge ------------------------------------------------------------------

# Haltungen aus dem Paper; Dateinamen in prompts/attitudes/
ATTITUDES = ("strict", "objective", "lenient")
# Lokales Modell (T4): weniger Haltungen in allen Stufen. Dauert es zu lange: auf ("strict",) kürzen.
LOCAL_ATTITUDES = ("strict", "lenient")

# Gewichte der Bewertungsdimensionen (prompts/scale_iso25010.md); Summe 1.0
WEIGHTS = {"functional_correctness": 0.40, "reliability": 0.20, "maintainability": 0.25, "readability": 0.15}

TEMPERATURE = 0.0  # Reproduzierbarkeit; Abweichung zum Paper (siehe prompts/ADAPTATION.md)
MAX_TOKENS = 2000
TIMEOUTS = {"openrouter": 90, "ollama": 180}  # Sekunden pro LLM-Aufruf
MAX_RETRIES = 3  # bei 429/5xx/Timeout, exponentieller Backoff im openai-SDK
CONCURRENCY = {"openrouter": 6, "ollama": 1, "mock": 4}

# --- Schritt 1: menschliches Gutachten ------------------------------------------

# Verdeckte Rollenkarte je Gruppe (prompts/role_cards_de.md); None = Kontrollgruppe ohne Rolle
HUMAN_ROLES = {"Gruppe 1": "strict", "Gruppe 2": "objective", "Gruppe 3": "lenient", "Gruppe 4": None}
HUMAN_SNIPPET = "bank_account"

# --- Prompt-Challenge -------------------------------------------------------

CHALLENGE_MAX_SUBMISSIONS = 3
POINTS = {"tp": 2, "fp_bug": -1}

# --- Scoreboard -------------------------------------------------------------

# Nach dem Deployment der Apps-Script-Web-App eintragen (scoreboard/DEPLOY.md).
# Leere URL: Läufe landen nur in der lokalen CSV-Sicherung.
SCOREBOARD_URL = "https://script.google.com/macros/s/AKfycbwXy2n88oda5nLpq1J2SVzG5J3D5SX0wPi82gtKlSvz2jdw5p1dIYabfz0ef8Ks9d19Zw/exec"
SCOREBOARD_TOKEN = "3551d940879490ee5fc93673928866b2"
DEFAULT_SESSION_ID = "rehearsal"
FINDINGS_JSON_MAX = 5000  # Zeichen
SCOREBOARD_TIMEOUT = 10  # Sekunden
SCOREBOARD_RETRIES = 2
