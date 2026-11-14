# software-quality-engineering

Hands-on „LLM-as-a-Judge für Softwarequalität“: Gruppen schreiben Judge-Prompts und lassen Code-Beispiele mit bekannten Fehlern über OpenRouter bewerten. Gemessen wird die Note für den Code (Code-Score) und wie gut das Modell die echten Fehler findet (Judge-Score). Die Ergebnisse erscheinen live auf einem Dashboard.

| Für wen | Anleitung |
|---|---|
| Notebook-Autorin: die vier Funktionen `verbinde`, `bewerte`, `bewerte_alle`, `sende` | [docs/BAUSTEINE.md](docs/BAUSTEINE.md) |
| Dashboard einrichten und testen | [docs/DASHBOARD_TEST.md](docs/DASHBOARD_TEST.md) |

```bash
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/python -m pytest
```

Lizenz: MIT ([LICENSE](LICENSE)). Drittinhalte (QuixBugs): [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
