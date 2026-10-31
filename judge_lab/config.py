"""Zentrale Konfiguration: Pfade, Modelle, Gruppen und Bewertungsparameter."""

from pathlib import Path

# Das Paket liegt flach im Repository; die Datenordner liegen daneben.
REPO_ROOT = Path(__file__).resolve().parent.parent
SNIPPETS_DIR = REPO_ROOT / "snippets"
PROMPTS_DIR = REPO_ROOT / "prompts"

# Haltungen aus dem Paper; Dateinamen in prompts/attitudes/
ATTITUDES = ("strict", "objective", "lenient")

# Gewichte der Bewertungsdimensionen (prompts/scale_iso25010.md); Summe 1.0
WEIGHTS = {"functional_correctness": 0.40, "reliability": 0.20, "maintainability": 0.25, "readability": 0.15}
