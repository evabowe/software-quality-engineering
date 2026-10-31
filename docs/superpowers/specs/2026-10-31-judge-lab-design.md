# Hands-on „LLM-as-a-Judge für Softwarequalität“ – Konzept & Implementierungsplan

**Stand:** 31.10.2026 · **Session:** 19.11.2026, 45 min Hands-on · **Verantwortlich Infrastruktur/roter Faden:** Eva
**Zweck dieses Dokuments:** Konzept für das Team und Arbeitsauftrag für die Implementierung (Claude Code in VS Code). Abschnitte 1–4 sind Konzept, 5–13 sind Implementierung.

---

## 1. Leitidee und roter Faden

Das Paper (Chou 2026, *AI-as-a-Judge for software quality assessment*, SQJ 34:48) untersucht 4 LLM-Judges × 3 Haltungen (strict / objective / lenient) und beantwortet drei Fragen:

- **RQ1** Wie konsistent sind verschiedene Judges? → nur moderat (ICC 0.46–0.57)
- **RQ2** Verändern Rollen-Prompts das Urteil? → stark (Cohen's d > 0.9)
- **RQ3** Beeinflusst Code-Komplexität die Scores? → ja, aber kleine bis mittlere Effekte

Das Paper verzichtet **bewusst auf eine Ground Truth** („machine psychometrics“): Es misst nur, *wie* Judges bewerten, nicht, *ob sie recht haben*.

**Unser Hands-on ist eine Mini-Replikation mit Ground Truth.** Wir verwenden Code mit **bekannten, dokumentierten Defekten** und können deshalb messen, was das Paper nicht misst: Recall und False Positives der Judges.

Roter Faden durch die Gesamtveranstaltung:

```
Theorie (Jessica) → Paper RQ1–3 (Alea) → Kritik: "keine Ground Truth" (Alea)
   → Hands-on: "Was sehen wir, wenn wir die Ground Truth kennen?" (Eva)
   → Auswertung: zurück zu RQ1–3 + eigene Zusatzbefunde
   → Abschluss: Wiederholung der Umfrage von Folie 5 („Würdest du einem LLM das Code-Review überlassen?“)
```

Eigene Zusatzfaktoren über das Paper hinaus:

1. **Ground Truth** → Recall / False Positives statt nur Scores
2. **Mit vs. ohne Tests als Kontext** → hilft Testcode dem Judge?
3. **Bekannter Benchmark (QuixBugs) vs. eigenes Beispiel (bank_account)** → Hinweis auf Data Contamination (QuixBugs ist seit 2017 öffentlich und vermutlich in den Trainingsdaten)
4. **Prompt-Challenge** → Prompt-Engineering für Fehlerfindung statt für Strenge

---

## 2. Ablauf der 45 Minuten (mit Methoden aus dem Methodenpool CAU Kiel)

| Zeit | Phase | Methode | Inhalt | Wer |
|---|---|---|---|---|
| 0–5 | Einstieg & Setup | – | QR-Code → Colab. 4 Zweiergruppen, jede Gruppe = ein Judge-Modell. Gruppe 4 startet sofort die Ollama-Zelle (Download läuft im Hintergrund). Setup-Zelle ausführen, Gruppe wählen. | Eva |
| 5–7 | Prognose | **Think-Pair-Share** (Think/Pair) | Jedes Paar beantwortet im Notebook 2 Prognosefragen (Dropdowns), die auf das Scoreboard gehen: (a) Welcher Judge findet die meisten Fehler? (b) Findet „strict“ mehr Fehler als „lenient“ – oder vergibt es nur schlechtere Noten? | Gruppen |
| 7–17 | **Auftrag 1: Replikation** | – | Ein Klick → Matrix: 6 Snippets × 3 Haltungen × {mit, ohne Tests}. Ergebnisse automatisch auf dem Scoreboard. Leitfragen im Notebook: Wie unterscheiden sich die Scores je Haltung? Ändert sich auch, was gefunden wird? | Gruppen, Eva betreut |
| 17–32 | **Auftrag 2: Prompt-Challenge** | – | Gruppen schreiben einen eigenen Judge-Prompt. Ziel: möglichst viele echte Defekte, möglichst wenige Fehlalarme, gute Erklärungen. Probeläufe unbegrenzt auf einem Snippet, **max. 3 offizielle Einreichungen** (laufen immer über alle 6 Snippets → Prompt muss generalisieren). Live-Leaderboard. | Gruppen, Eva + Jessica betreuen |
| 32–40 | Auswertung | **Vernissage** (digital) + **Share** | Scoreboard am Beamer: Heatmaps zu RQ1/RQ2/RQ3 und Zusatzfaktoren; Prognosen vs. Ergebnis. Prompt-Galerie: alle eingereichten Prompts nebeneinander; Gewinnergruppe erklärt ihren Prompt; Plenum stimmt über die beste Erklärung ab. | Eva moderiert, Alea ordnet ins Paper ein |
| 40–45 | Abschluss | **Blitzlicht** | Ein Satz pro Person: „Würde ich einen LLM-Judge in die CI einbauen – unter welcher Bedingung?“ + Wiederholung der Umfrage von Folie 5 (Vorher/Nachher). | alle |

Optional am Ende der gesamten 90 min (mit dem Team abstimmen): **Fünf-Finger-Methode** als Feedback zur Lehreinheit.

**Zeitpuffer:** Wenn Auftrag 1 länger dauert, wird Auftrag 2 auf 2 Einreichungen gekürzt. Die Auswertung (Phase 32–40) wird nicht gekürzt, weil sie die Brücke zum Paper ist.

---

## 3. Code-Beispiele (Vorauswahl, mit Jessica abzustimmen)

### 3.1 Quelle und Lizenz

- **QuixBugs** – https://github.com/jkoppel/QuixBugs, MIT-Lizenz, © 2017–2019 James Koppel.
  Referenz: Lin, Koppel, Chen, Solar-Lezama (2017): *QuixBugs: A Multi-Lingual Program Repair Benchmark Set Based on the Quixey Challenge*, SPLASH Companion.
  40 Programme, jeweils **genau ein einzeiliger Defekt**, korrigierte Version und Testfälle mitgeliefert.
- **bank_account** – eigenes Lehrbeispiel (Jessica), 3 semantische + 3 Code-Qualitäts-Defekte, dokumentiert in `src/code_with_defects/README.md`.

Die QuixBugs-Dateien werden **unverändert** übernommen (Zeilennummern bleiben gleich). Es werden keine Snippets von einem LLM generiert.

### 3.2 Auswahl: 5 Komplexitätsstufen + eigenes Beispiel

Kriterien: Streuung über die Komplexität (analog zu L1–L5 im Paper), unterschiedliche Defektklassen, kurze Programme (lesbar am Beamer), Docstring-Spezifikation vorhanden.

Die Komplexitätswerte sind eine eigene AST-Näherung; die finalen Werte berechnet `tools/compute_complexity.py` mit complexipy (siehe 6.2).

| ID | Programm | Stufe | Kogn. Komplexität (Näherung) | Defekt (Zeile im Originalfile) | Korrektur | Defekt-Typ |
|---|---|---|---|---|---|---|
| `qb_bitcount` | bitcount | L1 | ~1 | **Z. 5** `n ^= n - 1` | `n &= n - 1` | falscher Operator (führt zu Endlosschleife) |
| `qb_quicksort` | quicksort | L2 | ~3 | **Z. 7** `if x > pivot` | `if x >= pivot` (alternativ Z. 6 `<=`) | falscher Vergleichsoperator: Duplikate gehen verloren |
| `qb_levenshtein` | levenshtein | L3 | ~5 | **Z. 6** `return 1 + levenshtein(...)` | `return levenshtein(...)` | überzählige Arithmetik |
| `qb_shunting_yard` | shunting_yard | L4 | ~8 | **fehlende Zeile nach Z. 17** | `opstack.append(token)` im `else`-Zweig | fehlende Zeile (Defekt durch Abwesenheit) |
| `qb_next_permutation` | next_permutation | L5 | ~10 | **Z. 6** `if perm[j] < perm[i]` | `if perm[i] < perm[j]` | vertauschte Operanden im Vergleich |
| `bank_account` | eigenes Beispiel | – | 9 (complexipy) | 6 Defekte, s. 3.3 | s. README | gemischt |

Die Defektklasse laut QuixBugs-Paper (Tabelle 1) wird beim Übernehmen in `meta.yaml` nachgetragen.

**Begründung der Auswahl:**
- `bitcount` ist kurz, aber trickreich (Bit-Trick); der Defekt verursacht eine Endlosschleife → Tests brauchen einen Timeout.
- `quicksort` kennt jeder; der Fehler zeigt sich nur bei Duplikaten → gut für die Frage „hilft der Testkontext?“.
- `levenshtein` ist rekursiv; der Fehler ist eine Kleinigkeit in einer sonst korrekten Formel.
- `shunting_yard` ist didaktisch am wertvollsten: Der Defekt ist eine **fehlende Zeile**. Kann ein Judge etwas finden, das nicht da ist?
- `next_permutation` hat verschachtelte Schleifen und Indexlogik → höchste Komplexität.
- `bank_account` ist **nicht öffentlich** → Kontrolle für Data Contamination; enthält zusätzlich Code-Qualitäts-Defekte, die keine Tests brechen.

Ersatzkandidaten, falls Jessica tauschen möchte: `gcd` (L1, sehr bekannt), `rpn_eval` (L2), `kheapsort` (L2), `lis` (L4), `shortest_path_length` (L5+, 48 Zeilen – evtl. zu lang).

### 3.3 Ground Truth bank_account (aus README, geprüft gegen den Code)

| # | Zeilen | Art | Kurzbeschreibung |
|---|---|---|---|
| B1 | 26 | bug | `balance -= amount` in `deposit` |
| B2 | 31 | bug | `<=` statt `<` beim Dispo-Limit |
| B3 | 39–40 | bug | Reihenfolge Gutschrift/Abbuchung in `transfer` |
| Q1 | 24–25 | quality | toter `elif amount < 0`-Zweig |
| Q2 | 33 | quality | unerreichbarer Code nach `raise` |
| Q3 | 42 | quality | ungenutzter Parameter `days` |

Hinweis: Z. 38 enthält den Tippfehler „Überisung“. Er ist **nicht** Teil der Ground Truth. Ein Judge, der ihn meldet, bekommt dafür weder Punkte noch Abzug (Kategorie `style`, s. Matching-Regeln 6.5). Mit Jessica klären, ob er bleiben soll.

---

## 4. Messgrößen und Auswertung (Mapping auf das Paper)

| Dashboard-Ansicht | Paper-Bezug | Inhalt |
|---|---|---|
| **Heatmap Modell × Haltung: Ø Score** | RQ2 | Verschiebt die Haltung die Note? |
| **Heatmap Modell × Haltung: Recall** | RQ2 + Ground Truth | Verschiebt die Haltung auch die Fehlerfindung? (Kernfrage) |
| **Übereinstimmung der Judges** | RQ1 | Pro Defekt: welche Modelle haben ihn gefunden (Matrix Defekt × Modell); dazu Spearman-ρ der Scores zwischen Modellen |
| **Recall über Komplexitätsstufe** | RQ3 | Liniendiagramm L1–L5 je Modell |
| **Mit vs. ohne Tests** | Zusatz | Δ Recall und Δ False Positives |
| **QuixBugs vs. bank_account** | Zusatz (Validität) | Recall auf öffentlichen vs. unbekannten Code |
| **Prognose vs. Ergebnis** | Didaktik | Was hat die Gruppe erwartet? |
| **Leaderboard Prompt-Challenge** | Prompt Engineering | Punkte eigenes Modell + Punkte Referenzmodell |
| **Prompt-Galerie** | Vernissage | Alle eingereichten Prompts mit Punkten |

**Erwartbare Diskussionsthesen** (für Moderation vorbereiten, nicht vorab verraten):
- „strict“ senkt den Score deutlich, erhöht den Recall aber kaum → *Strenge ≠ Gründlichkeit*.
- „strict“ erzeugt mehr False Positives → Strenge kostet Präzision.
- Testkontext erhöht den Recall bei `quicksort`/`bank_account`, weil Testnamen die Absicht verraten.
- `shunting_yard` (fehlende Zeile) wird seltener gefunden.
- Kleines lokales Modell: deutlich weniger Recall, mehr Formatfehler → Trade-off Datenschutz vs. Qualität.

---

## 5. Architektur-Überblick

```
┌──────────────────────── Google Colab (pro Gruppe) ───────────────────────┐
│ hands_on.ipynb  (Low-Code: Formulare, Buttons, keine sichtbare Logik)    │
│   └── judge_lab (Python-Paket aus dem Repo)                              │
│        prompts → llm → parsing → matching → scoreboard                   │
│                   │                                                      │
│      ┌────────────┴─────────────┐                                        │
│      ▼                          ▼                                        │
│  OpenRouter API            Ollama lokal (nur Gruppe 4, T4-GPU)           │
│  (Gruppen 1–3, Referenz)   OpenAI-kompatibel: http://localhost:11434/v1  │
└───────────────────────────────┬──────────────────────────────────────────┘
                                │ HTTPS POST (JSON, mit Session-Token)
                                ▼
┌──────────────── Google Apps Script Web-App ─────────────────┐
│ doPost → Zeile in Google Sheet „runs“ anhängen               │
│ doGet  → Dashboard (HtmlService, Auto-Refresh) am Beamer     │
│ doGet?format=json → aggregierte Daten                        │
└──────────────────────────────────────────────────────────────┘
```

**Designentscheidungen:**
- **Ein OpenAI-kompatibler Client für alle Provider** (OpenRouter und Ollama sprechen beide das Chat-Completions-Format) → nur `base_url`, `api_key` und `model` unterscheiden sich.
- **Die gesamte Logik liegt im Paket `judge_lab`**, das Notebook enthält nur UI-Aufrufe. Dadurch ist die Logik testbar, und das Notebook bleibt low-code.
- **Matching im Client** (Python) – die Ground Truth liegt im Repo und wird **nie an das LLM gesendet** und vor der Auflösung nicht im Notebook angezeigt.
- **Mock-Provider** für Tests, Proben und als Notfall-Fallback (keine Kosten, deterministisch).

---

## 6. Repository-Struktur (Zielzustand)

```
software-quality-engineering/
├── README.md                     # Projektüberblick + „Open in Colab“-Badge
├── LICENSE                       # MIT (eigener Code)
├── THIRD_PARTY_NOTICES.md        # QuixBugs (MIT), ai-as-a-judge Prompts (MIT)
├── pyproject.toml                # Paket judge_lab + pytest-Konfiguration
├── notebooks/
│   ├── hands_on.ipynb            # Studierenden-Notebook (Colab)
│   ├── complexity.ipynb          # bisheriges main.ipynb, erweitert auf alle Snippets
│   └── instructor.ipynb          # Vorab-Läufe, Referenzläufe, Reset, Auflösung
├── judge_lab/
│   ├── __init__.py
│   ├── config.py                 # Modelle, Gruppen-Zuordnung, Gewichte, Limits
│   ├── snippets.py               # Snippet-Registry laden
│   ├── prompts.py                # Prompt-Komposition
│   ├── llm.py                    # Provider-Clients, Retries, Concurrency
│   ├── parsing.py                # JSON-Extraktion + Validierung
│   ├── matching.py               # Ground-Truth-Matching, Metriken
│   ├── scoring.py                # Gewichteter Gesamtscore, Challenge-Punkte
│   ├── scoreboard.py             # POST an Apps Script, lokaler CSV-Fallback
│   ├── runner.py                 # Matrix-Ausführung, Fortschritt
│   ├── ollama_colab.py           # Ollama installieren/starten/Modell ziehen
│   └── ui.py                     # ipywidgets-Formulare und Ergebnisanzeige
├── snippets/
│   ├── bank_account/
│   │   ├── code.py               # = src/code_with_defects/bank_account.py (unverändert)
│   │   ├── tests.py              # = bestehende Tests (unverändert)
│   │   └── meta.yaml             # Ground Truth, Quelle, Komplexität
│   ├── qb_bitcount/
│   │   ├── code.py               # QuixBugs python_programs/bitcount.py (unverändert)
│   │   ├── tests.py              # aus json_testcases generiert (s. 6.3)
│   │   └── meta.yaml
│   └── … (qb_quicksort, qb_levenshtein, qb_shunting_yard, qb_next_permutation)
├── prompts/
│   ├── original/                 # = src/role_prompts/* unverändert + SOURCE.md
│   ├── attitudes/{strict,objective,lenient}.md   # adaptierte Haltungsblöcke
│   ├── scale_iso25010.md         # Bewertungsskala (ersetzt VMA-Index)
│   ├── task_template.md          # Aufgabenbeschreibung + Platzhalter
│   ├── output_contract.md        # festes Ausgabeformat (nicht editierbar)
│   ├── challenge_baseline.md     # Startprompt für Auftrag 2
│   └── ADAPTATION.md             # Dokumentation: was wurde gegenüber dem Paper geändert und warum
├── scoreboard/
│   ├── Code.gs                   # Apps Script: doPost/doGet
│   ├── dashboard.html            # HtmlService-Dashboard
│   └── DEPLOY.md                 # Schritt-für-Schritt-Deployment
├── tools/
│   ├── import_quixbugs.py        # Snippets aus QuixBugs-Checkout übernehmen
│   └── compute_complexity.py     # complexipy → meta.yaml
├── tests/                        # Unit-Tests für judge_lab
└── docs/
    ├── CONCEPT.md                # Abschnitte 1–4 dieses Dokuments
    ├── GUIDE_STUDENTS.md         # 1 Seite für Teilnehmende
    ├── GUIDE_INSTRUCTOR.md       # Setup, Keys, Ollama, Generalprobe
    └── RUNBOOK.md                # Minutenplan am 19.11., Fallbacks
```

`src/code_with_defects/` und `src/role_prompts/` werden nach `snippets/bank_account/` bzw. `prompts/original/` verschoben (`git mv`, damit die Historie erhalten bleibt). **`src/code_with_defects/README.md` enthält die Lösung** → wandert nach `snippets/bank_account/SOLUTION.md` und wird im Notebook nie angezeigt.

### 6.1 `meta.yaml` (Schema)

```yaml
id: qb_quicksort
title: QuickSort
source:
  name: QuixBugs
  url: https://github.com/jkoppel/QuixBugs
  file: python_programs/quicksort.py
  commit: <hash beim Import>
  license: MIT
complexity:
  level: L2                 # manuell gesetzt, für Darstellung
  cognitive: 3              # von compute_complexity.py überschrieben
  loc: 14
spec: docstring             # Spezifikation steckt im Docstring des Codes
tests:
  origin: generated_from_json_testcases   # oder: original
  timeout_s: 5
defects:
  - id: D1
    kind: bug               # bug | quality
    lines: [7, 7]           # Hauptstelle
    accept_lines: [6, 7]    # Bereich, in dem ein Fund als Treffer zählt
    description: "Vergleich `x > pivot` verwirft Duplikate des Pivot-Elements"
    fix: "if x >= pivot"
    quixbugs_class: "<laut Paper Tabelle 1>"
```

Für `qb_shunting_yard`: `lines: [17, 18]`, `accept_lines: [15, 18]`, `kind: bug`, Beschreibung „fehlendes `opstack.append(token)` im else-Zweig“.

### 6.2 `tools/compute_complexity.py`
- Nutzt `complexipy.file_complexity` (wie das bestehende Notebook) und schreibt `complexity.cognitive` + `loc` in jede `meta.yaml`.
- `notebooks/complexity.ipynb` zeigt die Tabelle aller Snippets (bisheriges `main.ipynb`, erweitert).

### 6.3 `tools/import_quixbugs.py`
- Argument: Pfad zu einem QuixBugs-Checkout + Liste von Programmnamen.
- Kopiert `python_programs/<name>.py` **byte-identisch** nach `snippets/qb_<name>/code.py`.
- Erzeugt `tests.py` aus `json_testcases/<name>.json`: die ersten **6** Testfälle als lesbare pytest-Funktionen (`assert quicksort([1, 2, 6, 72, 7, 33, 4]) == [...]`). Begründung: Die Original-Testdateien laden nur JSON und wären für den Judge als Kontext nutzlos. Im Header von `tests.py` wird die Herkunft vermerkt.
- Schreibt den Commit-Hash in `meta.yaml`. Die Ground Truth wird **manuell** gepflegt (Tabelle 3.2), nicht automatisch erzeugt.

---

## 7. Prompt-Design

### 7.1 Problem
Die Rollen-Prompts aus dem Paper sind für **C++-Signalverarbeitung mit „Sensory Intent“** gebaut (VMA-Index 4.0: Recovery, Mapping mit α-Parametern, `vector::erase` …). Eingabe dort: „Original Prompt + C++ code“. Auf Python-Beispiele mit Algorithmen angewendet, würden die meisten Dimensionen ins Leere laufen.

### 7.2 Lösung: unabhängige Variable behalten, Messinstrument tauschen
Komposition jedes Judge-Prompts (Reihenfolge fest):

```
[1] Haltungsblock     ← prompts/attitudes/<attitude>.md   (Auftrag 1)  |  Text der Gruppe (Auftrag 2)
[2] Bewertungsskala   ← prompts/scale_iso25010.md
[3] Aufgabe           ← prompts/task_template.md mit {code_numbered}, {spec_hint}, {tests_block}
[4] Ausgabevertrag    ← prompts/output_contract.md   (immer angehängt, nicht editierbar)
```

**[1] Haltungsblöcke** – adaptiert aus dem Paper:
- Unverändert übernommen werden die **Rolle** (strict: „Chief Embedded Software Architect“, objective: „Senior System Engineer“, lenient: „Technical Product Manager / Rapid Prototype Developer“), die **Grundhaltung** (Skepsis / Pragmatismus / Toleranz) und die **Startpunktzahl** (strict 3, objective 5–6, lenient 7).
- Entfernt werden die domänenspezifischen Teile (sensorische Begriffe, α-Parameter, C++-Spezifika).
- Jede Änderung wird in `prompts/ADAPTATION.md` als Tabelle *Original → Adaptiert → Begründung* dokumentiert. Das ist gleichzeitig Material für Aleas Kritik-Teil.

**[2] Skala nach ISO/IEC 25010** (passt zum Modul Software Quality Engineering):

| Dimension | Gewicht | Prüffrage |
|---|---|---|
| Functional correctness | 40 % | Erfüllt der Code die Spezifikation (Docstring/Regeln)? |
| Reliability / Robustness | 20 % | Randfälle, Fehlerbehandlung, Terminierung |
| Maintainability | 25 % | toter/unerreichbarer Code, ungenutzte Parameter, Struktur |
| Readability | 15 % | Benennung, Klarheit, Kommentare |

Jede Dimension wird mit 0–10 bewertet und mit einem kurzen Ankertext pro Bereich (1–2 / 3–4 / 5–6 / 7–8 / 9–10) beschrieben. Den gewichteten Gesamtscore berechnet `scoring.py` selbst; der vom LLM gemeldete Gesamtwert wird nur zusätzlich gespeichert, weil LLMs beim Rechnen unzuverlässig sind.

**[3] Aufgabe:** Code **mit Zeilennummern** (`  7 | greater = …`), Hinweis „Die Spezifikation steht im Docstring bzw. Modul-Kommentar“, optional `{tests_block}`:
- *mit Tests:* „Folgende Tests beschreiben das erwartete Verhalten:“ + `tests.py`
- *ohne Tests:* Block entfällt vollständig

Für `bank_account` gilt: Der Modul-Docstring enthält die Regeln, die Tests heißen sprechend (z. B. `test_withdraw_exactly_to_limit_is_allowed`). Diese Hinweiswirkung ist gewollt und Teil des Faktors.

**[4] Ausgabevertrag** (JSON, auf Englisch formuliert, weil das mit allen Modellen am zuverlässigsten funktioniert):

```json
{
  "findings": [
    {
      "line_start": 7,
      "line_end": 7,
      "category": "bug | robustness | maintainability | style",
      "severity": "high | medium | low",
      "description": "what is wrong and why",
      "suggested_fix": "corrected code line(s)"
    }
  ],
  "scores": {"functional_correctness": 0, "reliability": 0, "maintainability": 0, "readability": 0},
  "overall_score": 0.0
}
```
Anweisung: „Antworte ausschließlich mit diesem JSON-Objekt, ohne Markdown-Fences.“ Bei OpenRouter `response_format={"type": "json_object"}` setzen, wenn das Modell es unterstützt; bei Ollama `format="json"`.

### 7.3 Auftrag 2: Challenge-Prompt
- Das Textfeld enthält `challenge_baseline.md` (objective-Haltung als Ausgangspunkt) und ersetzt **nur Block [1]**. [2]–[4] werden immer automatisch angehängt → das Format bleibt auswertbar.
- **Regel (im Notebook sichtbar):** Der Prompt muss für alle Snippets funktionieren und darf keine snippetspezifischen Hinweise enthalten. Durchgesetzt wird das durch die Vernissage (soziale Kontrolle) und einen einfachen Check, der bei Zeilennummern oder Funktionsnamen im Prompt warnt (nicht blockiert).

---

## 8. Modul-Spezifikation `judge_lab`

### 8.1 `config.py`
```python
GROUPS = {
  "Gruppe 1": {"model_key": "gemini"},
  "Gruppe 2": {"model_key": "deepseek"},
  "Gruppe 3": {"model_key": "kimi"},
  "Gruppe 4": {"model_key": "local"},
}
MODELS = {
  # IDs eine Woche vorher auf openrouter.ai/models prüfen und fixieren!
  "gemini":   {"provider": "openrouter", "id": "google/gemini-<aktuelle Flash-Version>", "label": "Gemini (wie im Paper)"},
  "deepseek": {"provider": "openrouter", "id": "deepseek/deepseek-<aktuelle Chat-Version>", "label": "DeepSeek (wie im Paper)"},
  "kimi":     {"provider": "openrouter", "id": "moonshotai/kimi-<aktuelle K2-Version>", "label": "Kimi (wie im Paper)"},
  "local":    {"provider": "ollama", "id": "qwen2.5-coder:3b", "label": "Qwen Coder 3B lokal (Colab T4)"},
  "reference":{"provider": "openrouter", "id": "<Referenzmodell, z. B. Qwen Coder groß>", "label": "Referenz"},
  "mock":     {"provider": "mock", "id": "mock", "label": "Mock (Probe)"},
}
ATTITUDES = ("strict", "objective", "lenient")
WEIGHTS = {"functional_correctness": .40, "reliability": .20, "maintainability": .25, "readability": .15}
TEMPERATURE = 0.0          # Reproduzierbarkeit; im RUNBOOK als Abweichung zum Paper vermerken
MAX_TOKENS = 2000
CONCURRENCY = {"openrouter": 6, "ollama": 1}
CHALLENGE_MAX_SUBMISSIONS = 3
POINTS = {"tp": 2, "fp_bug": -1}
```
Doubao (im Paper) ist auf OpenRouter voraussichtlich nicht verfügbar → durch das lokale Modell ersetzt; im Konzept als Abweichung dokumentieren.

**Ollama-Modell:** auf einer T4 testen. `qwen2.5-coder:3b` (~2 GB) ist der Standard, `qwen2.5-coder:7b` (~4,7 GB) nur, wenn Download und Inferenz in der Generalprobe schnell genug sind. Tags vorher auf ollama.com prüfen.

### 8.2 `snippets.py`
- `load_snippets() -> list[Snippet]` liest `snippets/*/meta.yaml`, `code.py`, `tests.py`.
- `Snippet.numbered_code()` → Code mit rechtsbündigen Zeilennummern, identisch zu den Zeilennummern der Ground Truth.
- `Snippet.public_view()` → alles **außer** `defects` (für UI und Prompt).

### 8.3 `prompts.py`
- `build_prompt(snippet, attitude=None, custom_block=None, with_tests: bool) -> list[messages]`
- System-Message = Blöcke [1]+[2]; User-Message = [3]+[4].
- `prompt_hash` (SHA-256, erste 12 Zeichen) für die Zuordnung auf dem Scoreboard.
- `lint_challenge_prompt(text) -> list[warnings]` (Zeilennummern, Funktionsnamen der Snippets).

### 8.4 `llm.py`
- `class ChatClient(base_url, api_key, model)`, `complete(messages) -> LLMResult(text, latency_s, tokens_in, tokens_out, error)`.
- Basis: `openai`-Python-SDK (OpenAI-kompatibel), OpenRouter `base_url="https://openrouter.ai/api/v1"`, Ollama `http://localhost:11434/v1`, `api_key="ollama"`.
- Retries: 3× mit exponentiellem Backoff bei 429/5xx/Timeout; Timeout 90 s (Ollama 180 s).
- Mock-Provider: liefert pro Snippet deterministische, plausible Findings (teils Treffer, teils FP, einmal kaputtes JSON) → testet die ganze Pipeline.
- Concurrency über `ThreadPoolExecutor` mit `CONCURRENCY[provider]`.

### 8.5 `parsing.py`
- `extract_json(text)`: entfernt Markdown-Fences und `<think>…</think>`-Blöcke, nimmt das erste balancierte `{…}`.
- Validierung mit `pydantic`; fehlende Felder bekommen Defaults, `line_start > line_end` wird getauscht, Zeilen außerhalb des Codes werden geklemmt.
- Bei Parse-Fehler: **ein** Reparatur-Retry („Gib nur valides JSON nach Schema zurück“), danach `parse_ok=False`. Der Lauf zählt dann als 0 Treffer und wird auf dem Scoreboard markiert, nicht verworfen. Formattreue ist selbst ein Befund, gerade beim kleinen lokalen Modell.

### 8.6 `matching.py` – Regeln
1. Ein Finding **trifft** Defekt D, wenn sich `[line_start, line_end]` mit `D.accept_lines` überschneidet.
2. Gibt es mehrere Kandidaten, gilt **exakte Überschneidung mit `D.lines` vor Toleranzbereich**, danach der kleinste Abstand. Jedes Finding trifft höchstens einen Defekt, jeder Defekt zählt höchstens einmal (greedy, deterministisch sortiert). Wichtig für `bank_account`, wo Z. 24–25 (Q1) und Z. 26 (B1) direkt nebeneinander liegen.
3. Ein Treffer zählt **unabhängig von der Kategorie** (ein Qualitätsdefekt, den das LLM als `bug` meldet, zählt trotzdem).
4. Ein **False Positive** ist ein nicht zugeordnetes Finding mit `category in {bug, robustness}`.
5. Nicht zugeordnete Findings mit `maintainability`/`style` sind **neutral** (angezeigt, nicht gewertet).
6. Metriken pro Lauf: `tp`, `fp`, `neutral`, `n_defects`, `recall = tp/n_defects`, `precision = tp/(tp+fp)` (bei 0/0 → leer).

Unit-Tests (Pflicht): benachbarte Defekte (bank_account Z. 24–26), Finding über mehrere Defekte hinweg, fehlende Zeile (shunting_yard Z. 17/18), leere Findings, Zeilen außerhalb des Codes.

### 8.7 `scoring.py`
- `weighted_score(scores) -> float` nach `WEIGHTS`.
- `challenge_points(runs) = Σ (2·tp − 1·fp)` über alle 6 Snippets.

### 8.8 `scoreboard.py`
- `submit(record: dict)` → POST JSON an `SCOREBOARD_URL` mit `token`. Timeout 10 s, 2 Retries.
- Bei Fehler: Zeile in `/content/scoreboard_backup.csv`, Warnung im UI (der Lauf geht nicht verloren; Eva kann die CSV nachträglich einspielen).
- `session_id` (z. B. `2026-11-19-live`, `rehearsal-1`) trennt Proben von der echten Session.

**Datensatz (eine Zeile pro LLM-Lauf):**
`timestamp, session_id, group, phase (prognosis|a1|a2_probe|a2_submit|reference), model_key, model_id, attitude, snippet_id, complexity_level, with_tests, prompt_hash, prompt_text (nur a2_submit), tp, fp, neutral, n_defects, recall, precision, weighted_score, llm_overall_score, scores_json, found_defect_ids, findings_json (gekürzt auf 5000 Zeichen), parse_ok, latency_s, tokens_in, tokens_out, notebook_version`

Prognose-Zeilen: `phase=prognosis`, `prediction_best_model`, `prediction_strict_vs_lenient`.

### 8.9 `runner.py`
- `run_matrix(group, snippets, attitudes, test_variants, on_progress)` → Liste von Records; sendet jeden Record sofort ans Scoreboard (Live-Effekt).
- Auftrag 1 Standard: 6 × 3 × 2 = **36 Läufe** (API-Gruppen).
- **Gruppe 4 (lokal), reduzierte Matrix:** 6 Snippets × {strict, lenient} × ohne Tests = 12 Läufe (in der Generalprobe Laufzeit messen; ggf. auf 6 reduzieren).
- `run_challenge(group, prompt_text, submit: bool)`: Probe = 1 Snippet nach Wahl, nicht gezählt. Submit = alle 6 Snippets, ohne Tests, mit dem Gruppenmodell **und** dem Referenzmodell (trennt Prompt-Effekt vom Modell-Effekt; Referenzläufe mit `phase=reference`). Zähler im UI: „Einreichung 1/3“.

### 8.10 `ollama_colab.py`
- `ensure_gpu()` prüft `nvidia-smi`; ohne GPU klare Meldung + Fallback-Angebot (Gruppe 4 nutzt dann ein kleines Modell über OpenRouter, damit die Bedingung „kleines Modell“ erhalten bleibt).
- `install()` mit dem offiziellen Installer (`curl -fsSL https://ollama.com/install.sh | sh`), `serve()` als Hintergrundprozess mit Log-Datei, `pull(model)` mit Fortschrittsanzeige, `warmup()` mit einer Mini-Anfrage.
- Idempotent (zweimal ausführen schadet nicht).

### 8.11 `ui.py` (ipywidgets)
- `setup_panel()`: Gruppe (Dropdown) → zeigt das zugeordnete Modell; API-Key: zuerst `google.colab.userdata.get("OPENROUTER_API_KEY")`, sonst Passwortfeld. Status „✅ Bereit – euer Judge: Kimi“.
- `prognosis_panel()`: 2 Dropdowns + „Absenden“.
- `assignment1_panel()`: Button „Auftrag 1 starten“, Fortschrittsbalken (x/36), danach Tabelle (pandas Styler): Zeilen = Snippet, Spalten = Haltung × Tests, Zellen = „Score · gefunden x/y“.
  **Vor der Auflösung wird nur angezeigt, *ob* und *wie viele* Defekte gefunden wurden, nicht *wo*.** Die Findings des LLM (Beschreibungen) sind sichtbar.
- `assignment2_panel()`: Textarea (Baseline vorbefüllt), Lint-Warnungen, Snippet-Dropdown + „Probelauf“, Button „Einreichen (1/3)“, Ergebnis: Punkte, Treffer je Snippet ✔/✘, FP-Anzahl.
- Alle Fehler werden als verständliche deutsche Meldung angezeigt, nie als Traceback (Traceback nur in einem einklappbaren Debug-Bereich).

---

## 9. Notebook `notebooks/hands_on.ipynb` (Zellenplan)

Alle Code-Zellen mit `#@title …` und `cellView: form` → in Colab eingeklappt; Studierende sehen nur Titel und Formulare.

| # | Typ | Titel | Inhalt |
|---|---|---|---|
| 0 | MD | Willkommen | Ziel, Ablauf (4 Schritte), Zeitplan, Link zum Scoreboard |
| 1 | Code | ⚙️ 1 · Setup (einmal ausführen) | `git clone` (öffentliches Repo), `pip install -q -e .`, `import judge_lab`, `ui.setup_panel()` |
| 2 | Code | 🖥️ Nur Gruppe 4: lokales Modell starten | `ollama_colab.ensure_gpu/install/serve/pull/warmup` |
| 3 | MD | Kurz erklärt: Was macht der Judge? | Schaubild der Prompt-Blöcke [1]–[4]; Hinweis auf das Paper |
| 4 | Code | 🔮 2 · Eure Prognose | `ui.prognosis_panel()` |
| 5 | Code | 🔍 Code ansehen (optional) | Dropdown → zeigt Snippet mit Zeilennummern und Docstring (ohne Ground Truth) |
| 6 | Code | 🧪 3 · Auftrag 1: Replikation | `ui.assignment1_panel()` |
| 7 | MD | Leitfragen Auftrag 1 | 3 Fragen zum Diskutieren im Paar |
| 8 | Code | 🏆 4 · Auftrag 2: Prompt-Challenge | `ui.assignment2_panel()` |
| 9 | MD | Tipps für gute Judge-Prompts | 5 Hinweise (Rolle, Prüfschritte, Randfälle, Spezifikation zuerst lesen, „nur sichere Befunde melden“) |
| 10 | MD | Abschluss | Link zur Umfrage, Dank |

`instructor.ipynb`: Vorab-Läufe aller Modelle (Backup-Daten mit `session_id=precomputed`), Referenzläufe, Auflösung (Ground Truth + Trefferübersicht pro Gruppe), CSV-Import in das Sheet, Kostenabfrage über die OpenRouter-API.

**Colab-Spezifika:**
- Das Repo muss **öffentlich** sein (oder ein öffentlicher Spiegel), sonst funktionieren Clone und „Open in Colab“-Badge ohne Login nicht. Vor der Veröffentlichung den OneDrive-Link aus der README entfernen.
- ipywidgets funktionieren in Colab nativ; bei Darstellungsproblemen `google.colab.output.enable_custom_widget_manager()`.
- Notebook-Version (`notebook_version`) als Konstante in `judge_lab/__init__.py`, damit man auf dem Scoreboard veraltete Kopien erkennt.

---

## 10. Scoreboard (Google Apps Script)

### 10.1 Sheet
- Tab `runs` (Kopfzeile = Datensatzfelder aus 8.8), Tab `config` (Token, aktive `session_id`), optional Tab `pivot` als Fallback-Ansicht mit `QUERY`/Pivot und bedingter Formatierung.

### 10.2 `Code.gs`
- `doPost(e)`: JSON parsen → Token prüfen → Felder in Kopfzeilenreihenfolge anhängen (`LockService`, damit gleichzeitige Posts keine Zeilen überschreiben) → `{status:"ok"}`.
- `doGet(e)`:
  - ohne Parameter → `HtmlService` liefert `dashboard.html`
  - `?format=json&session=<id>` → aggregierte Daten (Aggregation in Apps Script, damit das Dashboard schlank bleibt)
- Deployment: *Execute as: Me*, *Who has access: Anyone*. URL + Token kommen in `judge_lab/config.py` (Token ist kein echtes Geheimnis, verhindert aber Zufallsposts).

### 10.3 `dashboard.html`
- Lädt alle 10 s `?format=json`, Tabs/Abschnitte gemäß Tabelle in Abschnitt 4.
- Darstellung: einfache HTML-Tabellen mit Farbskala (Heatmaps) + Chart.js (CDN) für Recall über Komplexität. Große Schrift, beamertauglich, helles Theme.
- Session-Filter über URL-Parameter `?session=…`; Schalter „Vorab-Daten einblenden“ (precomputed) als Fallback.
- Ansicht „Auflösung“ erst nach Klick sichtbar (zeigt, welche Defekte wo lagen).

### 10.4 `DEPLOY.md`
Screenshots-freie Schrittliste: Sheet anlegen → Erweiterungen → Apps Script → Dateien einfügen → Deploy → URL testen mit `curl -X POST` (Beispiel-Payload im Dokument) → URL in `config.py`.

---

## 11. Kosten, Keys, Datenschutz

- **Budget:** 12 €. Abschätzung: ~3–4 k Tokens pro Lauf. Auftrag 1 ≈ 3 × 36 Läufe, Auftrag 2 ≈ 4 Gruppen × (Proben + 3 × 6 Läufe × 2 Modelle), plus 2 Proben und Vorab-Läufe → grob 2–3 Mio. Tokens → je nach Modellpreisen ca. 1–8 €.
- **Keys:** In OpenRouter **ein Key pro Gruppe** mit eigenem Kreditlimit (z. B. 2 $) + ein Instructor-Key. Verteilung über eine Folie bzw. einen QR-Code am Tag, **nie im Repo**. Nach der Session alle Keys widerrufen.
- **Datenschutz:** Es werden nur Gruppennamen gespeichert, keine personenbezogenen Daten. An die Provider geht nur der Beispielcode. Im Student-Guide kurz erwähnen, dass Daten an externe Anbieter gehen.

---

## 12. Tests und Qualitätssicherung der Infrastruktur

- `pytest` für `matching`, `parsing`, `prompts` (Snapshot der komponierten Prompts), `scoring`, `snippets` (jede `meta.yaml` valide; `accept_lines` innerhalb des Codes; Zeilen in `lines` zeigen auf nicht-leere Zeilen bzw. bei `missing line` auf die Einfügestelle).
- **Ground-Truth-Plausibilisierung:** Test, der für jedes QuixBugs-Snippet prüft, dass `code.py` byte-identisch zur Quelle (Commit-Hash) ist und dass die Original-Tests auf `code.py` fehlschlagen und auf der korrigierten Version durchlaufen (mit Timeout, wegen der Endlosschleife in `bitcount`). Das läuft lokal bzw. in CI, nicht in Colab.
- **End-to-End mit Mock-Provider:** komplette Matrix + Challenge gegen ein Test-Sheet (`session_id=ci`).
- **Generalprobe** in Colab mit echten Modellen, gemessen: Setup-Zeit, Dauer Auftrag 1 je Gruppe, Ollama-Download/Inferenzzeit, Kosten.

---

## 13. Arbeitspakete und Meilensteine

| Nr. | Paket | Ergebnis / Definition of Done | Bis |
|---|---|---|---|
| AP1 | Repo-Umbau | Neue Struktur, `git mv` der Bestandsdateien, `LICENSE`, `THIRD_PARTY_NOTICES.md`, `pyproject.toml` mit Paket `judge_lab` | 02.11. |
| AP2 | Snippets | `import_quixbugs.py`, 5 QuixBugs-Snippets + bank_account mit `meta.yaml`, `compute_complexity.py`, Plausibilisierungstest grün | 03.11. |
| AP3 | Prompts | Haltungsblöcke adaptiert, `ADAPTATION.md`, Skala, Task, Output-Vertrag, Baseline | 03.11. |
| AP4 | Kernlogik | `snippets`, `prompts`, `llm` (+Mock), `parsing`, `matching`, `scoring`, `runner` + Unit-Tests grün | 05.11. |
| **MVP** | **End-to-End** | **bank_account × 1 API-Modell × 3 Haltungen → CSV, in Colab lauffähig** (passt zum Team-Meilenstein 3.11.: „Eva macht Infrastruktur/Notebook vorbereiten“ – bis dahin mindestens AP1–AP3 + Durchstich mit Mock) | 03.–05.11. |
| AP5 | Scoreboard | `Code.gs`, `dashboard.html`, `DEPLOY.md`, Test-Sheet live, Mock-E2E schreibt ins Sheet | 08.11. |
| AP6 | Notebook-UI | `ui.py`, `hands_on.ipynb`, `instructor.ipynb`, Ollama-Zelle | 10.11. |
| AP7 | Doku | `GUIDE_STUDENTS.md` (1 Seite), `GUIDE_INSTRUCTOR.md`, `RUNBOOK.md` mit Fallbacks | 12.11. |
| AP8 | Generalprobe 1 | Mit Alea und Jessica in Colab, Messwerte + Bugliste | 13.11. |
| AP9 | Fixes + Modell-IDs fixieren | Keys anlegen, Vorab-Läufe (`precomputed`), Generalprobe 2 | 16.11. |
| — | Freeze | Keine Änderungen mehr an `main`, Tag `v1.0-session` | 17.11. |

### Reihenfolge für Claude Code
1. AP1 → AP2 → AP3 (Daten und Prompts zuerst, damit die Inhalte stehen)
2. AP4 mit Mock-Provider und Tests (testgetrieben, besonders `matching`)
3. AP5 Scoreboard (kann parallel getestet werden: `curl`-Payloads)
4. AP6 UI zuletzt, weil sie nur die fertigen Funktionen aufruft

### Leitplanken für die Implementierung
- Keine Snippets oder Defekte generieren. Code nur aus QuixBugs (unverändert) oder dem bestehenden bank_account.
- Die Ground Truth gelangt nie in einen Prompt oder vor der Auflösung in die UI. Ein Test prüft das (z. B. `assert "D1" not in build_prompt(...)` und keine `description`-Texte aus `meta.yaml` im Prompt).
- Abhängigkeiten minimal halten (`openai`, `pydantic`, `pyyaml`, `ipywidgets`, `pandas`, `requests`, `complexipy`), alle in Colab vorinstalliert oder schnell installierbar.
- Deutsch in der UI, Englisch im Code und in den Prompts an das LLM.

---

## 14. Risiken und Fallbacks

| Risiko | Wahrscheinlichkeit | Fallback |
|---|---|---|
| Keine T4-GPU für Gruppe 4 | mittel | Kleines Modell über OpenRouter (Bedingung „kleines Modell“ bleibt erhalten); Vorab-Daten für das lokale Modell im Dashboard |
| Ollama-Download zu langsam | mittel | 3B statt 7B; Download startet in Minute 0 |
| Rate-Limits / API-Ausfall | gering | Retries; anderes Modell im Dropdown; Mock-Modus; Vorab-Daten |
| Scoreboard nicht erreichbar | gering | Lokale CSV, später Import; Pivot-Tab im Sheet als Ansicht |
| WLAN-Probleme im Raum | gering–mittel | Hotspot; Dashboard mit Vorab-Daten als Screenshot-Folie |
| Studierende ohne Programmierkenntnisse kommen nicht weiter | mittel | Nur Formulare/Buttons, Student-Guide, Eva und Jessica gehen herum |
| JSON-Formatfehler beim lokalen Modell | hoch | Reparatur-Retry; `parse_ok=False` wird als Befund diskutiert |
| Zeitüberzug in Auftrag 1 | mittel | Auftrag 2 auf 2 Einreichungen kürzen; Auswertung bleibt vollständig |

---

## 15. Offene Punkte (Team)

1. Snippet-Auswahl mit Jessica bestätigen (Abschnitt 3.2), Tippfehler Z. 38 in bank_account klären.
2. Wer betreut am 19.11. welche Gruppen? Wer moderiert welche Auswertungsansicht? (Vorschlag: Eva Ablauf/Technik, Alea Paper-Bezug, Jessica Code/Defekte)
3. Kostenübernahme durch die Hochschule anfragen; sonst 4 € pro Person.
4. Repo öffentlich machen (OneDrive-Link vorher aus der README entfernen).
5. Fünf-Finger-Feedback am Ende der 90 min einplanen?
6. Abweichungen vom Paper (Doubao → lokales Modell, Temperatur 0, ISO-25010-Skala statt VMA) in Aleas Kritik-Folie aufnehmen.
