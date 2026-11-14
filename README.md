# software-quality-engineering

Hands-on „LLM-as-a-Judge für Softwarequalität“: Gruppen schreiben Judge-Prompts und lassen Code-Beispiele mit bekannten Fehlern über OpenRouter bewerten. Gemessen wird die Note für den Code (Code-Score) und wie gut das Modell die echten Fehler findet (Judge-Score). Die Ergebnisse erscheinen live auf einem Dashboard.

Dashboard URL: https://script.google.com/macros/s/AKfycbwXy2n88oda5nLpq1J2SVzG5J3D5SX0wPi82gtKlSvz2jdw5p1dIYabfz0ef8Ks9d19Zw/exec


```bash
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/python -m pytest
```

Lizenz: MIT ([LICENSE](LICENSE)). Drittinhalte (QuixBugs): [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
