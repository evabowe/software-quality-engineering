# Bausteine fürs Notebook

Für das Notebook gibt es genau vier Funktionen:

| Funktion | Wofür |
|---|---|
| `verbinde("K7QX")` | Code von der Folie eingeben → Gruppe und OpenRouter-Key sind gesetzt |
| `bewerte(prompt, snippet=…)` | ein Snippet mit dem Prompt der Gruppe bewerten lassen (Runde 1 und 2) |
| `bewerte_alle(prompt)` | alle fünf Snippets L1–L5 auf einmal bewerten lassen (Runde 3 und 4) |
| `sende(ergebnis, runde=…)` | Ergebnis ans Dashboard schicken, die Kachel der Gruppe aktualisiert sich |

Alles andere läuft im Hintergrund: OpenRouter, Bewertungsskala, Antwortformat, Abgleich mit den bekannten Fehlern, Google Sheet. Bei Fehlern sehen die Studierenden eine kurze deutsche Meldung, nie einen Traceback.

## 1. Einrichtung (lokal auf dem Rechner der Studierenden)

Einmal pro Rechner, im Terminal (Python ≥ 3.10):

```bash
git clone https://github.com/evabowe/software-quality-engineering
cd software-quality-engineering
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e . jupyterlab
jupyter lab notebooks/
```

Das Notebook gehört in den Ordner `notebooks/` des Repos. Die Snippets und Prompt-Bausteine liegen im Repo, deshalb reicht ein `pip install` ohne Klon nicht. In VS Code genügt `pip install -e . ipykernel`, dann `.venv` als Kernel wählen.

Erste Code-Zelle im Notebook:

```python
from judge_lab import verbinde, bewerte, bewerte_alle, sende
```

Kommt `ModuleNotFoundError: judge_lab`, läuft das Notebook nicht im Kernel der `.venv`.

## 2. Die Funktionen

### `verbinde(code)`

```python
verbinde("K7QX")          # → ✅ Verbunden als Gruppe 2.
```

- Groß-/Kleinschreibung und Leerzeichen sind egal. Danach kennen die anderen drei Funktionen Gruppe und Key.
- **Notfall** (Code-Server nicht erreichbar, steht dann in der Meldung): Key und Gruppe von der Notfall-Folie eintragen, also `verbinde(key="sk-or-…", gruppe="Gruppe 2")`.

### `bewerte(prompt, snippet="bank_account", modell="openai/gpt-6-luna")`

```python
ergebnis = bewerte("Du bist ein strenger Senior-Reviewer …", snippet="bank_account")
ergebnis["code_score"]    # 5.2  – Note des Modells für den Code, 0–10
ergebnis["judge_score"]   # 3    – wie gut das Modell als Gutachter war (max. ergebnis["judge_max"], hier 12)
ergebnis["gefunden"], ergebnis["fehler_gesamt"], ergebnis["fehlalarme"]   # 2, 6, 1
```

- **`prompt`** ist nur der Text der Gruppe, zum Beispiel eine Rolle oder Haltung. Skala, Code mit Zeilennummern und Antwortformat hängt die Funktion selbst an.
- **`code_score`** ist die gewichtete Note aus den vier ISO-25010-Dimensionen (0–10).
- **`judge_score`** gibt 2 Punkte für jeden echten Fehler, den das Modell gefunden hat, und zieht 1 Punkt für jeden Fehlalarm ab. Er kann negativ sein.
- **`modell`**: Jede OpenRouter-ID funktioniert, Standard ist GPT-6 Luna. Mit `modell="mock"` gibt es eine kostenlose Probe ohne `verbinde`, die nicht ans Dashboard geht.
- **Ground Truth:** `gefunden` gibt an, wie viele der `fehler_gesamt` bekannten Fehler das Modell gefunden hat. `fehlalarme` zählt gemeldete Bugs an Stellen ohne echten Fehler, reine Stil-Hinweise zählen nicht. `judge_max` = 2 × `fehler_gesamt`.
- **Rückgabe:** ein dict mit `code_score`, `judge_score`, `judge_max`, `gefunden`, `fehler_gesamt`, `fehlalarme`, `snippet`, `komplexitaet`, `modell`, `prompt`, `gruppe`, `einreichung` und `fehler`.
- **Fehler** (z. B. falscher Key, Guthaben leer, unlesbare Antwort): Es kommt eine Meldung, beide Scores sind `None` und `fehler` enthält den Grund. Einfach noch einmal ausführen.

### `bewerte_alle(prompt, modell="openai/gpt-6-luna")`

```python
ergebnisse = bewerte_alle("Du bist ein strenger Senior-Reviewer …")   # 1/5 fertig … 5/5 fertig
```

Die Funktion bewertet die fünf Snippets parallel und gibt eine Liste mit fünf dicts in der Reihenfolge L1 → L5 zurück. Fällt ein Snippet aus, laufen die anderen trotzdem weiter.

### `sende(ergebnis, runde)`

```python
sende(ergebnis, runde=2)      # → ✅ 1 Ergebnis(se) gesendet …
sende(ergebnisse, runde=4)    # → ✅ 5 Ergebnis(se) gesendet …
```

- **Runden:** 1 = Frei ausprobieren, 2 = Rollen vergleichen, 3 = Komplexität vergleichen, 4 = AI Challenge.
- **Runde 1 und 2** erwarten das Ergebnis von `bewerte`, **Runde 3 und 4** die Liste von `bewerte_alle`. Bei einer Verwechslung kommt ein Hinweis, und es wird nichts gesendet.
- Fehlgeschlagene Snippets und Mock-Ergebnisse werden nicht gesendet.
- Ist das Dashboard nicht erreichbar, wird lokal gesichert und beim nächsten `sende` automatisch nachgeholt.
- Dasselbe Ergebnis noch einmal zu senden (z. B. Zelle doppelt ausgeführt) schadet nicht: Es zählt nur einmal.

## 3. Beispiele je Runde

```python
# Runde 1 – Frei ausprobieren
ergebnis = bewerte("Prüfe den Code gründlich auf Fehler.", snippet="bank_account")
sende(ergebnis, runde=1)

# Runde 2 – Rollen vergleichen (jede Bewertung einzeln senden; die Kachel zeigt die letzte)
streng = bewerte("Du bist ein strenger Auditor …")
sende(streng, runde=2)
milde = bewerte("Du bist ein wohlwollender Mentor …")
sende(milde, runde=2)

# Runde 3 – Komplexität vergleichen
ergebnisse = bewerte_alle("Du bist ein erfahrener Reviewer …")
sende(ergebnisse, runde=3)

# Runde 4 – AI Challenge: finalen Prompt auf allen fünf Snippets
finale = bewerte_alle(mein_prompt)
sende(finale, runde=4)
```

Vorlagen gibt es bewusst nicht: Die Studierenden schreiben jeden Prompt selbst. In Runde 2 liegt der Fokus darauf, dem Modell eine Rolle zu geben.

## 4. Die Snippets

| `snippet` | Stufe | Inhalt |
|---|---|---|
| `bank_account` | – | Bankkonto (eigenes Beispiel, nicht aus QuixBugs; Kontrolle für Data Contamination) |
| `qb_bitcount` | L1 | Bits zählen |
| `qb_quicksort` | L2 | QuickSort |
| `qb_levenshtein` | L3 | Levenshtein-Distanz |
| `qb_shunting_yard` | L4 | Infix → RPN |
| `qb_next_permutation` | L5 | nächste Permutation |

`bewerte_alle` nutzt die fünf Snippets mit Stufe, `bank_account` gehört nicht dazu.

## 5. Was am Dashboard passiert

Die Lehrenden wählen am Beamer die Runde (Reiter oder Tasten 1–4). Jede Gruppe hat eine Kachel:

- **Runde 1, 2:** Judge-Score (von max.), Code-Score (von 10), „✔ 2 von 6 echten Fehlern gefunden · ✘ 1 Fehlalarm“ und der Prompt der zuletzt gesendeten Bewertung.
- **Runde 3:** ein Diagramm L1 → L5 mit Code-Score (links) und Judge-Score (rechts, gestrichelt das Maximum), darunter „gefunden 3 von 5 · 1 Fehlalarm“.
- **Runde 4:** Judge-Score, Maximum und Treffer summiert über die fünf Snippets, Code-Score als Durchschnitt. Die beste Gruppe ist hervorgehoben.

Über den Kacheln steht in jeder Runde, was Code-Score und Judge-Score bedeuten.

Neue Ergebnisse erscheinen nach höchstens 10 Sekunden.
