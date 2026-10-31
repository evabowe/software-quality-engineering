# software-quality-engineering

Hands-on „LLM-as-a-Judge für Softwarequalität“ (Session am 19.11.2026): eine Mini-Replikation von Chou (2026), *AI-as-a-Judge for software quality assessment*, **mit Ground Truth**. LLM-Judges bewerten sechs Code-Beispiele mit bekannten Defekten in drei Haltungen (strict / objective / lenient); gemessen werden Score, Recall und Fehlalarme. Danach schreiben die Gruppen in einer Prompt-Challenge eigene Judge-Prompts.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/evabowe/software-quality-engineering/blob/main/notebooks/hands_on.ipynb)

## Dokumentation

| Für wen | Dokument |
|---|---|
| Team: Idee, Ablauf, Messgrößen, Abweichungen | [docs/CONCEPT.md](docs/CONCEPT.md) |
| Teilnehmende (1 Seite) | [docs/GUIDE_STUDENTS.md](docs/GUIDE_STUDENTS.md) |
| Lehrende: Vorbereitung, Keys, Generalprobe | [docs/GUIDE_INSTRUCTOR.md](docs/GUIDE_INSTRUCTOR.md) |
| Ablauf am 19.11. und Fallbacks | [docs/RUNBOOK.md](docs/RUNBOOK.md) |
| Scoreboard deployen | [scoreboard/DEPLOY.md](scoreboard/DEPLOY.md) |
| Adaption der Prompts aus dem Paper | [prompts/ADAPTATION.md](prompts/ADAPTATION.md) |

## Aufbau

```
judge_lab/        Python-Paket: Snippets, Prompts, LLM-Clients, Parsing, Matching, Scoring, Scoreboard, Runner, UI
snippets/         6 Code-Beispiele: 5 aus QuixBugs (unverändert) + bank_account; je Code, Tests, meta.yaml (Ground Truth)
prompts/          Haltungsblöcke, Bewertungsskala (ISO/IEC 25010), Aufgabe, Ausgabevertrag; Original-Prompts aus dem Paper
notebooks/        hands_on.ipynb (Colab, Studierende), instructor.ipynb, complexity.ipynb
scoreboard/       Google-Apps-Script-Web-App: Code.gs + Beamer-Dashboard
tools/            QuixBugs-Import, Komplexitätsmessung
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

## Team-Notizen

Hier ist der Link zur Präsentation, die auf dem aktuellen Stand ist: https://1drv.ms/p/c/0f7867713b3d1e05/IQDp1p1jexXiSL4MY5R_2UW_AYRcZM5fm02LfodZ8ihTOqc?e=cWSFL0

noch TO DO:
Präsentation:
- Inhalt: siehe Kommentare in der Präsentation
- Klärung, wer präsentiert was
- Umfrage erstellen 
- final Check


Praxisteil:
- wer ist für was verantwortlich?
- Notebook, wie stellen wir Code bereit oder sogar APIS?
- wer übernimmt welchen Teil am VL Tag?
