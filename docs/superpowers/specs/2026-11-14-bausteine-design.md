# Design: Vier Bausteine für Jessicas Notebook

Stand: 14.11.2026 · Autorin der Anforderungen: Eva · Nutzerin der Bausteine: Jessica

## Warum

Das fertige Setup mit eigener Notebook-Oberfläche (Reiter, Phasenfreigabe, Rollenkarten, lokales Modell) kam im Team nicht an. Jessica baut das Notebook komplett selbst neu; wie, steht erst ab dem 15.11. fest. Evas Aufgabe ist die Technik darunter: Jessica soll **genau vier Funktionen** bekommen, die sie ohne Kenntnis der Interna aufrufen kann, und eine Anleitung, die erklärt, wie sie sie verwendet. Alles andere (OpenRouter-Zugang, Prompt-Aufbau, Parsing, Bewertung, Google Sheet, Dashboard) läuft im Hintergrund.

Erfolg heißt: Jessica liest die Anleitung, kopiert die Setup-Zelle und ruft die vier Funktionen in ihren Blöcken auf. Die Kacheln am Beamer aktualisieren sich, ohne dass sie oder die Studierenden etwas über Sheets, Tokens oder JSON wissen müssen.

## Die vier Funktionen (festgelegt)

```python
verbinde("K7QX")                                   # Code von der Folie → Gruppe + Key
ergebnis = bewerte(prompt, snippet="bank_account")  # → {"code_score": 5.2, "judge_score": 3, …}
sende(ergebnis, runde=2)                           # → Sheet, Dashboard-Kachel aktualisiert sich
ergebnisse = bewerte_alle(prompt)                  # Runde 3: alle 5 Snippets parallel
```

Import: `from judge_lab import verbinde, bewerte, bewerte_alle, sende`.

### `verbinde(code)`
- Löst den 4-stelligen Code von der Folie über den vorhandenen Code-Server (`?action=join` in `scoreboard/Code.gs`, Tab `keys`) in **Gruppenname + OpenRouter-Key** auf. Das gibt es heute schon in `judge_lab/join.py` und wird weiterverwendet.
- Merkt sich Gruppe und Key für die übrigen drei Funktionen (Modulzustand). Gibt eine kurze deutsche Bestätigung aus („Verbunden als Gruppe 2“).
- Groß-/Kleinschreibung und Leerzeichen im Code sind egal (vorhandene Normalisierung).
- *Unsere Entscheidung:* Notfallweg über optionale Parameter `verbinde(key="sk-or-…", gruppe="Gruppe 1")`, wenn der Code-Server nicht erreichbar ist. Ein Aufruf ohne Code, aber mit Key und Gruppe, setzt beides direkt.
- *Unsere Entscheidung:* Die bisherige Prüfung „Gruppe muss in `GROUPS` stehen“ entfällt. Als Gruppenname gilt, was im Tab `keys` steht, sodass das Team die Gruppen beliebig benennen kann.

### `bewerte(prompt, snippet="bank_account", modell="openai/gpt-6-luna")`
- `prompt` ist **nur der Text der Studierenden**, z. B. eine Rolle oder Haltung. Die Funktion setzt den vollständigen Judge-Prompt wie heute in `judge_lab/prompts.build_prompt(custom_block=…)` zusammen: Studierenden-Text und ISO-25010-Skala als System-Message, Aufgabe mit nummeriertem Code und Ausgabevertrag als User-Message. Ohne den Ausgabevertrag liefert das LLM keine Zeilennummern und der Judge-Score ist nicht berechenbar.
- `snippet` ist der Ordnername unter `snippets/`: `bank_account`, `qb_bitcount`, `qb_quicksort`, `qb_levenshtein`, `qb_shunting_yard`, `qb_next_permutation`. Bei einem unbekannten Namen kommt eine Meldung mit der Liste der gültigen Namen.
- `modell` ist eine beliebige OpenRouter-Modell-ID. Standard ist `openai/gpt-6-luna` (am 14.11.2026 in der OpenRouter-Modellliste vorhanden). Eine Liste fester Modelle gibt es nicht mehr.
- Es wird nur OpenRouter verwendet. Ollama und lokale Modelle fallen komplett weg. Der Mock-Client bleibt für Tests (`modell="mock"`).
- Ablauf intern: LLM-Aufruf (`temperature=0`, JSON-Modus), bei unlesbarer Antwort genau ein Reparatur-Versuch (vorhandene Logik aus `runner.judge`), tolerantes Parsen (`parsing.py`) und Abgleich der Findings mit der Ground Truth (`matching.py`).
- **Rückgabe:** ein dict
  ```python
  {"code_score": 5.2, "judge_score": 3,
   "snippet": "bank_account", "modell": "openai/gpt-6-luna", "prompt": "…",
   "gruppe": "Gruppe 2", "fehler": None}
  ```
  - `code_score`: die Note des LLM für den Code, 0–10, gewichtet aus den vier ISO-Dimensionen (`scoring.weighted_score`, Gewichte in `config.WEIGHTS`). `None`, wenn eine Dimension fehlt.
  - `judge_score`: wie gut das LLM als Gutachter war, **2 Punkte pro echtem Defekt, −1 pro Fehlalarm** (Kategorie `bug` auf einer Zeile ohne Defekt), gemessen an der Ground Truth des Snippets (`config.POINTS`, `scoring.challenge_points`). Kann negativ sein. Gewählt statt Recall, weil sich Recall durch Melden jeder Zeile hochtreiben lässt.
  - Die übrigen Felder braucht `sende`, damit Jessica nichts doppelt angeben muss.
- **Fehler** (falscher Key, Kreditlimit, Netz, Timeout, kein lesbares JSON auch nach der Reparatur) brechen nicht mit Traceback ab. Die Funktion gibt eine deutsche Meldung aus und liefert das dict mit `code_score=None`, `judge_score=None` und `fehler="…"`. Ein solcher Lauf zählt nicht als „0 Fehler gefunden“.
- Ohne vorheriges `verbinde` kommt die Meldung „Bitte zuerst `verbinde("CODE")` mit dem Code von der Folie ausführen.“ Nur beim Mock-Modell ist kein `verbinde` nötig.

### `bewerte_alle(prompt, modell="openai/gpt-6-luna")`
- Gedacht für **Runde 3 (Komplexität) und Runde 4 (AI Challenge)**. Beide laufen auf allen Snippets (Evas Entscheidung vom 14.11.).
- Ruft `bewerte` für die **fünf Snippets mit Komplexitätsstufe** auf (L1 `qb_bitcount`, L2 `qb_quicksort`, L3 `qb_levenshtein`, L4 `qb_shunting_yard`, L5 `qb_next_permutation`), **parallel** (bis zu 6 gleichzeitig, wie `config.CONCURRENCY["openrouter"]`).
- `bank_account` ist nicht dabei: Es hat keine Stufe und dient als Kontrolle für Data Contamination. *Unsere Entscheidung:* Das gilt auch für die Challenge, damit beide Runden dieselben fünf Snippets nutzen. „Alle Snippets“ heißt hier also die fünf QuixBugs-Snippets.
- Rückgabe: Liste der fünf dicts, sortiert nach Stufe L1→L5. Jedes dict hat zusätzlich `"komplexitaet": "L1"` usw. und eine gemeinsame `"einreichung"` (uuid des Aufrufs). Fällt ein Snippet aus, steht der Fehler in dessen dict; die anderen laufen weiter.
- *Unsere Entscheidung:* kurze Fortschrittsanzeige in Textform („3/5 fertig“), keine Widgets.

### `sende(ergebnis, runde)`
- `ergebnis` ist ein dict aus `bewerte` **oder** die Liste aus `bewerte_alle`. `runde` ist 1–4:
  1 = Frei ausprobieren, 2 = Rollen vergleichen, 3 = Komplexität vergleichen, 4 = AI Challenge.
- Schickt **eine Zeile pro Ergebnis** an die Apps-Script-Web-App (vorhandenes `scoreboard.Scoreboard` mit Retries und CSV-Sicherung).
- Runden 1 und 2 erwarten ein einzelnes Ergebnis, Runden 3 und 4 die Liste aus `bewerte_alle`. Passt es nicht, kommt ein kurzer Hinweis wie „Für Runde 4 bitte das Ergebnis von `bewerte_alle` senden“, und nichts wird gesendet.
- Ergebnisse mit `fehler` werden nicht gesendet; die Funktion sagt das in einer Meldung. Bei einer Liste werden die übrigen trotzdem gesendet.
- *Unsere Entscheidung:* Ergebnisse vom Mock-Modell werden nicht gesendet (Hinweis „Mock-Ergebnisse gehen nicht ans Dashboard“), damit Proben das Dashboard nicht verfälschen.
- Bei Erfolg kommt „✅ gesendet – das Dashboard zeigt es in ein paar Sekunden“, bei Ausfall „⚠️ Dashboard nicht erreichbar, lokal gesichert“ (CSV unter `/content/scoreboard_backup.csv`).
- *Unsere Entscheidung:* Jeder `sende`-Aufruf versucht zuerst, gesicherte Zeilen nachzusenden. Eine eigene Funktion dafür gibt es nicht, denn es bleibt bei genau vier Funktionen.
- `runde` außerhalb 1–4 ergibt eine deutsche Meldung, nichts wird gesendet.

## Datenvertrag Python → Sheet (Tab `runs`)

Abgestimmt mit Jessica waren Gruppenname, Score, Modell, Prompt und Snippet-Name. Durch die zwei Scores und die Runde wird daraus:

| Feld | Quelle |
|------|--------|
| `timestamp` | Python, UTC ISO |
| `run_id` | Python, uuid; das Dashboard entfernt doppelt gesendete Zeilen |
| `session_id` | **Apps Script setzt es** beim Empfang aus dem Tab `config` (Python kennt keine Sessions mehr) |
| `gruppe` | aus `verbinde` |
| `runde` | 1–4, aus `sende` |
| `snippet` | Snippet-ID |
| `komplexitaet` | L1–L5 oder leer (für die X-Achse in Runde 3) |
| `einreichung` | uuid eines `bewerte_alle`-Aufrufs; bei `bewerte` eine eigene uuid. Fasst die fünf Zeilen einer Einreichung in Runde 3 und 4 zusammen |
| `modell` | OpenRouter-ID |
| `prompt` | Text der Studierenden |
| `code_score` | 0–10 |
| `judge_score` | ganze Zahl, auch negativ |

Die Feldliste steht identisch in Python (`RECORD_FIELDS`) und `Code.gs` (`FIELDS`); der vorhandene Vertragstest (`tests/test_scoreboard_contract.py`) prüft das weiter. **Eva muss Jessica sagen, dass es 7 statt 5 inhaltliche Felder sind** (zwei Scores plus Runde). Die übrigen Felder setzt das System selbst.

*Unsere Entscheidung:* Das neue `Code.gs` schreibt in einen neuen Tab `runs` mit der neuen Kopfzeile. Gibt es im Sheet einen alten `runs`-Tab mit den 34 Spalten, wird er nicht weiterverwendet. Die Anleitung für Eva sagt, dass sie ihn vorher in `runs_alt` umbenennen soll.

## Dashboard (Apps-Script-Web-App, neu und schlank)

Am 14.11. mit Eva im Browser-Entwurf abgestimmt (`.superpowers/brainstorm/…/dashboard-layout.html`).

- **Reiter oben: 1 Frei · 2 Rollen · 3 Komplexität · 4 AI Challenge.** Die Lehrenden klicken am Beamer, Tasten 1–4 gehen auch. Das Dashboard springt nicht von selbst um.
- **Vier Gruppen-Kacheln (2×2)** für die gewählte Runde, eine pro Gruppe.
  - **Runden 1, 2, 4:** Gruppenname, Judge-Score und Code-Score groß, darunter der Prompt (gekürzt, ganz lesbar per Klick oder Tooltip – Builder entscheidet), darunter klein Snippet · Modell · „vor 2 min“. Es zählt nur die **zuletzt gesendete** Zeile der Gruppe in dieser Runde. Ohne Zeile ist die Kachel ausgegraut mit „noch nichts gesendet“.
  - **Runde 3:** In jeder Kachel ein Diagramm. X-Achse: L1–L5 mit dem Snippet-Namen als Beschriftung. Linke Y-Achse: Code-Score (0–10). Rechte Y-Achse: Judge-Score. Zwei Linien mit Punkten, darunter der Prompt. Es zählt die **zuletzt gesendete Einreichung** der Gruppe in Runde 3, also alle Zeilen mit derselben `einreichung`.
  - **Runde 4:** Aufbau wie in den Runden 1 und 2, aber für die zuletzt gesendete Einreichung der Gruppe: **Judge-Score = Summe über die fünf Snippets** (wie die heutige Challenge-Wertung `2·TP − FP`), **Code-Score = Durchschnitt**, darunter der Prompt. Fehlgeschlagene Snippets fehlen in Summe und Durchschnitt. Die Kachel zeigt dann klein „4/5 Snippets“.
  - *Unsere Entscheidung:* In Runde 4 ist die Kachel mit dem höchsten Judge-Score hervorgehoben, damit am Beamer ein Sieger erkennbar ist. Die Kacheln behalten ihre feste Reihenfolge.
- **Welche Kacheln:** die Gruppen aus dem Tab `keys` mit `active = TRUE`, in der Reihenfolge dort. Das sind in der Session vier, mehr oder weniger würden auch funktionieren.
- *Unsere Entscheidung:* Eine Kachel zeigt „verbunden“, sobald die Gruppe `verbinde` ausgeführt hat (vorhandenes Join-Protokoll im Tab `joins`). So sehen die Lehrenden vor dem ersten Senden, wer dabei ist.
- Das Dashboard lädt die Daten regelmäßig neu (Intervall wie heute bzw. Builder entscheidet, Ziel: unter ~10 s bis zur Anzeige).
- Gefiltert wird auf die aktive `session_id` aus dem Tab `config`. Nach der Probe genügt ein neuer Wert dort, und das Dashboard ist leer.
- **Fällt weg:** Phasenfreigabe und Admin-Modus, Rollen aufdecken, Paper-Vergleich, Heatmaps, RQ-Auswertungen, Prognosen, Ground-Truth-Upload und Tab `defects`, Vorab-Daten.

## Branch und Merge

Die Arbeit läuft **direkt auf `feature/interactive-session`** (Evas Entscheidung), denn nur dort gibt es `join.py` und den Code-Server. Am Ende wird **noch am 14.11. abends nach `main` gemergt**. Die Setup-Zelle in Jessicas Anleitung klont deshalb `main`. Der Merge ersetzt, was heute auf `main` liegt. Was entfernt wird, bleibt in der Git-Historie.

## Was aus dem Repo verschwindet

- **Python:** `ui.py`, `app.py`, `human.py`, `phase.py`, `instructor.py`, `ollama_colab.py`. `runner.py` schrumpft auf die Reparatur-Logik bzw. geht in das neue Modul über. `config.py` verliert Modelle/Gruppen/Ollama/Rollen/Phasen und bekommt `DEFAULT_MODEL = "openai/gpt-6-luna"`.
- **Notebooks: werden nicht angefasst** (Evas Vorgabe, Jessicas Bereich). Alle Dateien in `notebooks/` bleiben unverändert, ebenso `tools/build_notebooks.py`. **Folge:** `hands_on*.ipynb` und `instructor.ipynb` importieren entfernte Module und laufen danach nicht mehr. Das ist gewollt, Jessica ersetzt sie. `tests/test_notebooks.py` wird gelöscht, weil es die alten Notebooks gegen die alte Oberfläche prüft. `complexity.ipynb` und `tests/test_compute_complexity.py` bleiben, wenn sie ohne die entfernten Module laufen (Builder prüft).
- **Prompts:** `role_cards_de.md` (menschliche Rollenkarten) entfällt. Die Haltungsblöcke `prompts/attitudes/*.md` und `challenge_baseline.md` **bleiben** als Textvorlagen, die Jessica in „Rollen vergleichen“ oder der Challenge den Studierenden zeigen kann. `prompts/ADAPTATION.md`, `prompts/original/` und `THIRD_PARTY_NOTICES.md` bleiben (*unsere Entscheidung:* Sie belegen Herkunft und Änderungen der übernommenen Paper-Prompts, das verlangt die Lizenz).
- **Tests:** Tests zu entfernten Modulen werden gelöscht. Tests zu behaltenen Modulen (parsing, matching, scoring, prompts, snippets, join, scoreboard, ground truth) bleiben. Dazu kommen Tests für die vier Funktionen (mit Mock-Client und gefälschtem HTTP) und Node-Tests für die neue Aggregation in `Code.gs`.
- **Abhängigkeiten:** `ipywidgets` entfällt. `pandas`/`complexipy` nur, wenn `complexity.ipynb` sie noch braucht.
- **Doku, so weit wie möglich reduziert** (Evas Vorgabe): Gelöscht werden `docs/CONCEPT.md`, `docs/GUIDE_INSTRUCTOR.md`, `docs/GUIDE_STUDENTS.md`, `docs/RUNBOOK.md`, `docs/plans/` (inkl. Dashboard-Screenshots), `docs/superpowers/*/2026-10-31-judge-lab*` und `scoreboard/DEPLOY.md` (geht in Evas Anleitung auf). `README.md` wird auf wenige Zeilen gekürzt: was das Repo ist und Links auf die zwei Anleitungen. Dieses Design und der zugehörige Plan bleiben unter `docs/superpowers/`.

## Was neu entsteht

- `judge_lab/bausteine.py` (Name Builder-Sache): die vier Funktionen, exportiert in `judge_lab/__init__.py`.
- **Anleitung für Jessica** `docs/BAUSTEINE.md`, auf Deutsch, für jemanden, der Python im Notebook kann, aber das Repo nicht kennt:
  - Setup-Zelle zum Kopieren (Klon des Repos in Colab und Installation, nach Vorbild der heutigen Startzelle).
  - Je Funktion: wofür, Parameter, Rückgabe, ein Beispiel pro Runde.
  - Was die Studierenden bei Fehlern sehen.
  - Liste der Snippet-Namen mit Stufe.
  - Was im Sheet und auf dem Dashboard passiert.
- **Anleitung für Eva** `docs/DASHBOARD_TEST.md`: Sheet und Apps-Script einrichten bzw. neu deployen (ersetzt `DEPLOY.md`), Tabs `runs`, `config` (token, session_id), `keys`, `joins`, Codes im Tab `keys` anlegen. Dazu ein Testablauf: Mit dem Test-Notebook alle vier Runden einmal durchspielen und prüfen, dass jede Kachel richtig erscheint, dann `session_id` zurücksetzen.
- `scoreboard/Code.gs` und `scoreboard/dashboard.html` neu.
- **Test-Notebook nur für Eva:** `notebooks/eva_test.ipynb` mit je einem Aufruf jeder Funktion für alle vier Runden. **Wird nicht committet.** Es wird lokal über `.git/info/exclude` ignoriert, nicht über `.gitignore`, damit auch der Ignore-Eintrag nicht ins Repo kommt.
- Ein Notebook für Jessica gibt es nicht. Sie bekommt nur die Anleitung.

## Constraints

- Läuft in Google Colab (Python ≥ 3.10) und lokal. Colab klont `main` von GitHub.
- Die Snippet-Tests gehen nicht in den Prompt (`with_tests=False` fest).
- Scoreboard-URL und Token stehen wie heute in `config.py` (öffentliches Repo; das Token schützt nur vor Zufallstreffern). Keys werden nie ins Repo oder ins Sheet `runs` geschrieben.
- Kosten: GPT-6 Luna ≈ 0,10 $ pro Mio. Input-Tokens, also unkritisch. Pro Gruppe ein Key mit kleinem Kreditlimit (wie bisher).
- Apps Script ist langsam (~1–2 s pro Request). Bei `bewerte_alle` → `sende` gehen fünf Zeilen raus; der Builder darf sie in einem Request bündeln, wenn `doPost` dafür eine Liste annimmt.

## Ansätze

1. **Vorhandenes Paket ausdünnen (gewählt).** Was nicht mehr gebraucht wird, fliegt raus. Getestetes bleibt: Join, Prompt-Aufbau, JSON-Reparatur, Parsing, Ground-Truth-Abgleich, CSV-Sicherung. Neu sind die vier Funktionen und ein schlankes Dashboard. Gewählt, weil die Robustheit gegen LLM-Unsinn erhalten bleibt und das Repo trotzdem klein wird.
2. Komplett neu als eine Datei. Leichter zu lesen, aber Parsing und Abgleich müssten neu geschrieben werden und deren Tests gingen verloren.
3. Alles behalten, Fassade obendrauf. Am wenigsten Arbeit, aber das abgelehnte Setup bliebe im Repo, und das alte Dashboard passt nicht zu den neuen Feldern.

## Ziele, Nicht-Ziele, Anti-Ziele

- **Ziele:** genau vier Funktionen mit einer verständlichen Anleitung. OpenRouter ist der einzige Provider, Standardmodell GPT-6 Luna. Das Dashboard aktualisiert sich live nach Evas Entwurf.
- **Nicht-Ziele:** Jessicas Notebook-Inhalte und Didaktik, Folien, Widgets/Oberfläche, Phasensteuerung, Auswertungen über die Kacheln hinaus.
- **Anti-Ziele:** Jessica muss Interna kennen (Tokens, URLs, JSON, Sheet-Spalten). Ein Fehler eines LLM zeigt den Studierenden einen Traceback. Fehlgeschlagene Läufe erscheinen am Beamer als Score 0. Es entsteht eine fünfte öffentliche Funktion oder eine Oberfläche, die Jessicas Notebook vorgreift.

## Dem Builder überlassen

Modulname, interne Aufteilung, Reload-Intervall und Diagramm-Bibliothek des Dashboards (Chart.js ist heute schon eingebunden), wie der lange Prompt in der Kachel lesbar wird, ob `doPost` Listen annimmt, Formulierung der Meldungen (deutsch, kurz, ohne Fachjargon).

## Nachtrag 14.11. abends (nach Evas Live-Test, mit Eva abgestimmt)

1. **Antwortlimit:** GPT-6 Luna ist ein Reasoning-Modell; seine Denk-Tokens zählen in `max_tokens`. Mit 2000 wurde die Antwort bei strengen Rollen-Prompts abgeschnitten (gemessen: `finish_reason=length`, 1875 Reasoning-Tokens). `MAX_TOKENS` steigt auf 16000 (gemessen: max. ~2500 gebraucht; Kosten ≤ 0,01 $ pro Aufruf). Wird eine Antwort trotzdem abgeschnitten, meldet `bewerte` das ausdrücklich („Antwort abgeschnitten“) statt „nicht lesbar“.
2. **Keine Prompt-Vorlagen:** Die Studierenden schreiben alle Prompts selbst; in Runde 2 liegt der Fokus darauf, eine Rolle zu vergeben. Entfernt werden `prompts/attitudes/`, `prompts/original/`, `prompts/ADAPTATION.md`, `prompts/challenge_baseline.md`, `prompts/tests_block.md`, der Parameter `with_tests` und alles zu Haltungen im Code sowie der Abschnitt „ai-as-a-judge“ in `THIRD_PARTY_NOTICES.md` (Evas Vorgabe: kein Code im Repo, der nicht gebraucht wird).
3. **Ground Truth am Dashboard:** `bewerte` liefert zusätzlich `gefunden` (echte Fehler gefunden), `fehler_gesamt` (bekannte Fehler im Snippet), `fehlalarme` und `judge_max` (= 2 × `fehler_gesamt`); diese vier Felder gehen auch ans Sheet.
   - Kacheln Runde 1/2: „Judge-Score 3 von max. 12 · Code-Score 5,2 von 10 · ✔ 2 von 6 echten Fehlern gefunden · ✘ 1 Fehlalarm“. Runde 4: dieselben Werte summiert über die fünf Snippets.
   - Runde 3: Judge-Achse fest von 0 bis zum Maximum pro Snippet (2), gestrichelte Linie „max.“, darunter „gefunden 3 von 5 · 2 Fehlalarme“.
   - In jeder Runde über den Kacheln eine Erklärung: Code-Score = Note des Modells für den Code (0–10); Judge-Score = 2 Punkte je gefundenem echten Fehler, −1 je Fehlalarm, gemessen an den bekannten Fehlern.
   - Fehlalarm = gemeldeter Bug ohne echten Fehler an der Stelle; reine Stil-Hinweise zählen nicht.
4. **Skala ohne Anker (Variante B):** `prompts/scale_iso25010.md` nennt nur noch die vier Dimensionen mit Kernfrage und den Bereich 0–10. Die Anker-Tabelle („5–6 = …“) und die Gewichte im Prompt entfallen, weil sie festlegten, welche Note welches Verhalten bedeutet, und damit die Rollen der Studierenden übersteuerten. Gewichtet wird weiter in Python (`config.WEIGHTS`).
5. **Kein Colab mehr:** Die Studierenden klonen das Repo und arbeiten lokal (`pip install -e .`, Notebook in `notebooks/`). Entfernt: alle alten Notebooks (`hands_on*.ipynb`, `instructor.ipynb`, `complexity.ipynb`), `tools/build_notebooks.py`, der `/content`-Sonderfall der CSV-Sicherung, der `.installed`-Eintrag in `.gitignore` und die Abhängigkeit `pandas`. Die Vorgabe „Notebooks nicht anfassen“ ist damit aufgehoben (Eva, 14.11.).
