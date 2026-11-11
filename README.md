# software-quality-engineering

Hands-on „LLM-as-a-Judge für Softwarequalität“ (Session am 19.11.2026): eine Mini-Replikation von Chou (2026), *AI-as-a-Judge for software quality assessment*, **mit Ground Truth**. Zuerst begutachten die Studierenden selbst ein Code-Beispiel in einer verdeckten Rolle, dann bewerten LLM-Judges denselben Code und fünf weitere Beispiele mit bekannten Defekten in drei Haltungen (strict / objective / lenient); gemessen werden Score, Recall und Fehlalarme. Zum Schluss schreiben die Gruppen in einer Prompt-Challenge eigene Judge-Prompts. Ablauf: 75 Minuten, eine Notebook-Zelle, danach nur Reiter und Buttons.

| Gruppen 1–3 | Gruppe 4 (lokales Modell, mit GPU) |
|---|---|
| [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/evabowe/software-quality-engineering/blob/main/notebooks/hands_on.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/evabowe/software-quality-engineering/blob/main/notebooks/hands_on_gpu.ipynb) |

## Dokumentation

| Für wen | Dokument |
|---|---|
| Team: Idee, Ablauf, Messgrößen, Abweichungen | [docs/CONCEPT.md](docs/CONCEPT.md) |
| Teilnehmende (1 Seite) | [docs/GUIDE_STUDENTS.md](docs/GUIDE_STUDENTS.md) |
| Lehrende: Vorbereitung, Keys, Generalprobe | [docs/GUIDE_INSTRUCTOR.md](docs/GUIDE_INSTRUCTOR.md) |
| Ablauf am 19.11. und Fallbacks | [docs/RUNBOOK.md](docs/RUNBOOK.md) |
| Umbau auf die interaktive Session, offene Fragen | [docs/plans/](docs/plans/) |
| Scoreboard deployen | [scoreboard/DEPLOY.md](scoreboard/DEPLOY.md) |
| Adaption der Prompts aus dem Paper | [prompts/ADAPTATION.md](prompts/ADAPTATION.md) |

## Aufbau

```
judge_lab/        Python-Paket: Snippets, Prompts, LLM-Clients, Parsing, Matching, Scoring, Scoreboard, Runner, UI (app.py: Reiter)
snippets/         6 Code-Beispiele: 5 aus QuixBugs (unverändert) + bank_account; je Code, Tests, meta.yaml (Ground Truth)
prompts/          Haltungsblöcke, Bewertungsskala (ISO/IEC 25010), Aufgabe, Ausgabevertrag; Original-Prompts aus dem Paper
notebooks/        hands_on.ipynb (Colab, Studierende), hands_on_gpu.ipynb (Gruppe 4), instructor.ipynb, complexity.ipynb
scoreboard/       Google-Apps-Script-Web-App: Code.gs + Beamer-Dashboard
tools/            QuixBugs-Import, Komplexitätsmessung, GPU-Notebook bauen, Dashboard-Vorschau
tests/            pytest-Suite (inkl. maschineller Prüfung der Ground Truth)
```

Die Ground Truth steht in `snippets/*/meta.yaml` und `snippets/bank_account/SOLUTION.md`. Sie wird nie an ein LLM gesendet und im Studierenden-Notebook nicht angezeigt.

## Entwicklung

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/python -m pytest
```

Die Suite prüft auch, dass die Original-Tests jedes Snippets fehlschlagen und mit den dokumentierten Korrekturen grün werden, und führt die Node-Tests der Scoreboard-Aggregation aus (sofern Node installiert ist). Details: [docs/GUIDE_INSTRUCTOR.md](docs/GUIDE_INSTRUCTOR.md).

Lizenz: MIT ([LICENSE](LICENSE)); Drittinhalte (QuixBugs, Rollen-Prompts aus ai-as-a-judge): [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
