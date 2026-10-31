"""Zentrale Konfiguration: Pfade, Modelle, Gruppen und Bewertungsparameter."""

from pathlib import Path

# Das Paket liegt flach im Repository; die Datenordner liegen daneben.
REPO_ROOT = Path(__file__).resolve().parent.parent
SNIPPETS_DIR = REPO_ROOT / "snippets"
PROMPTS_DIR = REPO_ROOT / "prompts"
