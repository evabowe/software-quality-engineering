# Plan: Repo-Umbau für die interaktive 75-Minuten-Session

**Repo:** `evabowe/software-quality-engineering` · **Stand:** 11.11.2026 · **Session:** 19.11.2026 · **Code-Freeze:** 17.11.2026 (Tag `v1.0-session`)
**Zielgruppe dieses Dokuments:** Claude Code (Umsetzung) und Eva (Abnahme, Tests).
**Ablage im Repo:** `docs/plans/2026-11-11-interaktive-session.md` (diese Datei), danach umsetzen.

---

## 0. Warum der Umbau?

Neue Vorgaben der Dozentin:

- höchstens **75 min** gesamt
- so **interaktiv und anwendungsorientiert** wie möglich, Vortrag minimal
- mindestens **2 didaktische Methoden aus dem Methodenpool**, die keine andere Gruppe nutzt
- Unsere Wahl (vorbehaltlich Freigabe): **Gutachten erstellen** und **AI Challenge**, optional **Heißer Stuhl**

Der jetzige Code ist für „45 min Theorie + 45 min Hands-on“ gebaut: ein Klick startet eine 36er-Matrix, die Gruppen schauen dann vor allem zu. Neu soll die Session **aufbauend** sein: Erst urteilen die Studierenden selbst, dann urteilt das LLM über denselben Code, dann alle Snippets, zum Schluss die Prompt-Challenge.

Ein zweites Ziel ist, **Notebook und Dashboard so einfach wie möglich** zu machen: eine Zelle, ein Gruppencode, danach nur noch Buttons.

## 1. Zielablauf (Referenz für alle Arbeitspakete)

| Min. | Phase | Methode | Notebook-Schritt | Dashboard-Ansicht | `phase`-Wert im Record |
|---|---|---|---|---|---|
| 0–5 | Ankommen, Setup, Vorher-Umfrage (Menti) | Clicker | **Start**: Gruppencode eingeben | Status: „4/4 Gruppen verbunden“ | – |
| 5–15 | ① Ihr seid der Judge | **Gutachten erstellen** | **Schritt 1**: Rollenkarte lesen, `bank_account` bewerten (Zeilen + Score + Begründung) | „Mensch: Scores nach Rolle“ | `human` |
| 15–20 | Mini-Input LLM-as-a-Judge (Folien) | – | – | – | – |
| 20–32 | ② Gleicher Code, LLM als Judge | – | **Schritt 2**: Prognose → `bank_account` × 3 Haltungen → Vergleich Mensch vs. LLM → **Schritt 3**: restliche Snippets im Hintergrund | „Mensch vs. LLM“, Heatmaps RQ2 | `prognosis`, `a1` |
| 32–44 | ③ Paper vs. wir (RQ2), Kritik | Heißer Stuhl (optional) | – (Matrix läuft ggf. noch) | „Paper vs. wir“ | – |
| 44–64 | ④ Prompt-Challenge | **AI Challenge** | **Schritt 4**: Probelauf / Einreichen (max. 3) | Leaderboard, Prompt-Galerie | `a2_probe`, `a2_submit`, `reference` |
| 64–70 | Auflösung, Prognose-Check, Nachher-Umfrage | Clicker | **Schritt 5**: Abschluss (Link zur Umfrage) | „Auflösung“, „Prognose vs. Ergebnis“ | – |
| 70–75 | Blitzlicht + Ausblick | Blitzlicht | – | – | – |

Gruppen: 4 Zweiergruppen, Gruppe 1 = Gemini, 2 = DeepSeek, 3 = Kimi, 4 = lokales Modell (Ollama, T4). Daran ändert sich nichts.

**Rollenkarten für ① (verdeckt, eine pro Gruppe):** Gruppe 1 = strict, Gruppe 2 = objective, Gruppe 3 = lenient, Gruppe 4 = keine Rolle (Kontrollgruppe). Die Texte sind deutsche Kurzfassungen der Haltungsblöcke aus `prompts/attitudes/*.md` (Rolle, Grundhaltung, Startpunktzahl).

---

## 2. Leitplanken (gelten für alle Arbeitspakete)

1. **Keine neuen Snippets oder Defekte erzeugen.** Bestehende Snippets und `meta.yaml` bleiben unverändert.
2. **Die Ground Truth gelangt nie in einen Prompt und vor der Auflösung nie in die UI.** Das gilt auch für den neuen Mensch-Schritt: Nach der Eingabe sehen die Studierenden „x von 6 gefunden“, aber **nicht welche**.
3. **API-Keys stehen nie im Repo.** Der bestehende Test (keine `sk-or-…` in Notebooks) bleibt und wird auf alle neuen Dateien ausgeweitet.
4. Deutsch in UI und Doku, Englisch in Code-Bezeichnern und LLM-Prompts.
5. **Keine neuen Abhängigkeiten.** Alles läuft mit `ipywidgets`, `pandas`, `requests` und den vorhandenen Paketen.
6. Jede Änderung ist mit Tests abgesichert; `pytest` und `node --test scoreboard/aggregate.test.mjs` bleiben grün.
7. **Zuverlässigkeit vor Komfort:** Jede neue Online-Abhängigkeit (Gruppencode, Phasenfreigabe) hat einen Offline-Fallback, der ohne Rückfrage greift.
8. `NOTEBOOK_VERSION` in `judge_lab/__init__.py` bei jeder Änderung am Notebook-Verhalten hochzählen.

---

## 3. Arbeitspakete

Priorität: **P1 = muss bis 14.11.**, P2 = sollte bis 15.11., P3 = nur wenn Zeit bleibt. Reihenfolge der Umsetzung: AP1 → AP2 → AP3 → AP4 → AP5 → AP6 → AP7 → AP8.

### AP1 (P1) – Ein-Zellen-Notebook mit Schritt-für-Schritt-Oberfläche

**Ziel:** Studierende führen **genau eine Zelle** aus. Danach führt eine Oberfläche mit nummerierten Schritten durch die Session.

- `notebooks/hands_on.ipynb` wird auf **zwei Zellen** reduziert:
  1. Markdown „Willkommen“ (3 Sätze: worum es geht, „Klickt auf ▶ in der Zelle darunter“, Hinweis auf den Colab-Warndialog „Trotzdem ausführen“).
  2. Code-Zelle `#@title ▶ Start – hier klicken` mit eingeklapptem Code (`cellView: form`): Klon, Install, `from judge_lab import app; app.show()`.
- Neues Modul `judge_lab/app.py`: `show()` baut ein `widgets.Tab` (oder `Accordion`) mit den Reitern
  **Start · 1 Gutachten · 2 LLM-Judge · 3 Alle Beispiele · 4 Challenge · 5 Abschluss**.
  - Reiter, die noch nicht freigegeben sind (siehe AP5), zeigen „🔒 Kommt gleich – wartet auf das Signal vorne“.
  - Oben dauerhaft eine Statuszeile: `Gruppe 2 · Judge: DeepSeek · Scoreboard ✅ · Schritt 2 von 5`.
- Die vorhandenen Panels aus `ui.py` werden wiederverwendet und nur neu angeordnet. `ui.py` behält seine getesteten Aktionsfunktionen; die Panel-Funktionen dürfen angepasst werden.
- Die bisherigen Leitfragen und Tipps (Markdown-Zellen) wandern als kurze HTML-Blöcke in die jeweiligen Reiter.
- Fehler erscheinen weiterhin als deutsche Meldung, Tracebacks nur im eingeklappten Debug-Bereich.
- Wird die Zelle ein zweites Mal ausgeführt, kommt kein neuer Klon und keine Neuinstallation. Die Oberfläche erscheint mit dem bisherigen Zustand (`SESSION` bleibt erhalten).

**Akzeptanz:** Ein Test führt `app.show()` mit Mock aus und prüft, dass alle Reiter existieren, die gesperrten Reiter den Sperrtext zeigen und `test_notebooks.py` die 2-Zellen-Struktur sowie `cellView: form` prüft.

### AP2 (P1) – Gruppencode statt Gruppe + API-Key

**Ziel:** Studierende tippen **nur einen kurzen Code** (z. B. `K7Q2`) von der Folie ab. Gruppe, Modell und Key ergeben sich daraus.

- **Sheet:** neuer Tab `keys` mit den Spalten `code | group | openrouter_key | active`. Dieser Tab ist **nicht öffentlich**; das Sheet bleibt privat, nur die Web-App liest ihn.
- **`Code.gs`:** neuer GET-Endpunkt `?action=join&code=K7Q2&token=…` → `{status:"ok", group:"Gruppe 2", key:"sk-or-…"}`, ansonsten `{status:"error", message:"Code unbekannt"}`. Codes sind groß/klein-unabhängig, Leerzeichen werden entfernt.
- **`app.py` – Reiter „Start“:** ein Textfeld „Gruppencode“ und der Button „Los geht's“. Danach wird `ui.configure(group, key)` aufgerufen. Bei Erfolg erscheint `✅ Ihr seid Gruppe 2 – euer Judge heißt DeepSeek`.
- **Fallback (eingeklappt unter „Erweitert“):** die bisherigen Felder Gruppe (Dropdown) + API-Key + „Probemodus (Mock)“ + „Gruppe 4 ohne GPU“. Ist das Scoreboard nicht erreichbar, klappt der Bereich automatisch auf und zeigt den Hinweis „Code-Server nicht erreichbar – bitte Gruppe und Key von der Notfall-Folie eintragen“.
- Colab-Secret `OPENROUTER_API_KEY` wird weiterhin unterstützt (hat Vorrang vor dem Feld, nicht vor dem Code).
- `docs/GUIDE_INSTRUCTOR.md`: Abschnitt „Gruppencodes anlegen“ (Codes aus 4 Zeichen ohne verwechselbare Zeichen wie 0/O, 1/I; pro Session neu; Keys nach der Session widerrufen und Tab leeren).

**Akzeptanz:** Unit-Tests für die Code-Normalisierung und die Fehlermeldungen (HTTP-Mock). Node-Test für `join` in `aggregate.test.mjs` oder einer neuen Testdatei. Ein Test stellt sicher, dass `join` ohne gültiges `token` nichts herausgibt.

### AP3 (P1) – Schritt 1: Menschliches Gutachten (Methode „Gutachten erstellen“)

**Ziel:** Jede Gruppe bewertet `bank_account` zuerst selbst, in ihrer verdeckten Rolle. Ihr Ergebnis wird mit derselben Logik gemessen wie die LLM-Judges.

- `config.py`: `HUMAN_ROLES = {"Gruppe 1": "strict", "Gruppe 2": "objective", "Gruppe 3": "lenient", "Gruppe 4": None}` und `HUMAN_SNIPPET = "bank_account"`.
- Neue Datei `prompts/role_cards_de.md`: vier kurze deutsche Rollenkarten (je max. 5 Zeilen: Rolle, Haltung, „Starte bei … Punkten“). Die Karte für Gruppe 4 lautet: „Bewertet nach eurem eigenen Urteil.“ Die Texte werden aus `prompts/attitudes/*.md` abgeleitet, ohne inhaltlich etwas hinzuzufügen.
- Reiter „1 Gutachten“ zeigt:
  1. die Rollenkarte der Gruppe mit dem Hinweis **„Nicht verraten!“**
  2. den Code mit Zeilennummern (`snippet_html`, ohne Ground Truth)
  3. Eingaben: **Zeilen mit Fehlern** (Textfeld, Format `26, 31, 39-40`), **Score 1–10** (Slider), **Begründung in einem Satz** (Textfeld)
  4. Button „Gutachten abgeben“ (einmalig; danach gesperrt mit dem Hinweis „abgegeben“, Korrektur über „Erweitert“)
- Neue Funktion `judge_lab/human.py: parse_lines(text) -> list[Finding]`. Jede Angabe wird ein Finding mit `category="bug"`. Ungültige Eingaben ergeben eine verständliche Meldung.
- Danach wird gemessen wie beim LLM (`matching.py` unverändert) und als Record mit `phase="human"`, `attitude=<Rolle oder "none">`, `model_key="human"`, `weighted_score=<Slider>` und der Begründung in `findings_json` gespeichert.
- Rückmeldung an die Gruppe: „Ihr habt x von 6 Defekten gefunden, y Meldungen waren keine Defekte.“ **Ohne Zeilenangaben.**

**Akzeptanz:** Tests für `parse_lines` (Bereiche, Duplikate, Leerzeichen, Unsinn, Zeilen außerhalb des Codes), für den Record (`phase=human`) und dafür, dass keine Defektbeschreibung aus `meta.yaml` in der Ausgabe steht.

### AP4 (P1) – Schritte 2 und 3: aufbauende Läufe statt Ein-Klick-Matrix

**Schritt 2 „LLM-Judge“** (Reiter „2 LLM-Judge“):
1. **Prognose** (vorhandenes `prognosis_panel`, Texte angepasst):
   - H1: „Findet *strict* mehr echte Fehler als *lenient* – oder vergibt es nur schlechtere Noten?“ (die drei bisherigen Optionen)
   - H2: „Welcher Judge findet die meisten Defekte?“ (bisheriges Dropdown, zusätzlich Option „wir Menschen“)
2. Button **„Unseren Judge bewerten lassen“** → `run_matrix(ctx, client, [bank_account], ATTITUDES, (False,))`, also 3 Läufe; beim lokalen Modell nur strict + lenient.
3. Ergebnis als **Vergleichstabelle**, Zeilen = *Ihr (Rolle)*, *LLM strict*, *LLM objective*, *LLM lenient*; Spalten = Score · gefunden x/6 · Fehlalarme · Begründung (erste 200 Zeichen der LLM-Findings bzw. euer Satz).
4. Drei Leitfragen darunter: Wo liegt euer Score im Vergleich? Verschiebt die Rolle beim LLM nur die Note oder auch die Treffer? Hat das LLM etwas gefunden, das ihr übersehen habt (oder umgekehrt)?

**Schritt 3 „Alle Beispiele“** (Reiter „3 Alle Beispiele“):
- Button **„Restliche Beispiele starten“** → die 5 QuixBugs-Snippets × Haltungen × **ohne Tests**. Das sind 15 Läufe (API) bzw. 10 Läufe (lokal). Sie laufen **im Hintergrund-Thread**, damit die Gruppe in der Paper-Phase zuhören kann; ein Fortschrittsbalken bleibt sichtbar.
- Danach erscheint die bekannte Tabelle (`assignment1_table`) für alle 6 Snippets.
- **Bonus-Button** (nur API-Gruppen): „Bonus: mit Tests als Kontext“ → 6 × 3 × mit Tests = 18 Läufe.
- `assignment1_variants()` wird zu `stage_variants(model_key, stage)` umgebaut; die bisherige Funktion bleibt als Wrapper, damit die Tests weiterlaufen.
- `phase` bleibt `"a1"` für alle Läufe aus Schritt 2 und 3. Die Dashboard-Aggregation funktioniert also ohne Änderung weiter.

**Akzeptanz:** Tests für die Anzahl der Jobs je Stufe und Provider, dafür, dass Schritt 3 die Kombinationen aus Schritt 2 nicht wiederholt, und für den Hintergrund-Lauf mit Mock (Thread endet, Records sind vollständig).

**Optional (P3) – Streuung/H3:** Button „3× wiederholen“ in Schritt 2 mit `temperature=0.7` (Paper-nah). Records erhalten `phase="a1_repeat"`. Wird das nicht umgesetzt, müssen „Streuung“ und H3 von den Folien gestrichen werden; Eva entscheidet.

### AP5 (P2) – Phasenfreigabe durch die Lehrenden

**Ziel:** Alle Gruppen bleiben im Takt. Die Lehrenden schalten die Reiter vom Dashboard aus frei.

- Sheet-Tab `config`: neue Zeile `phase` (Werte `0`–`5`).
- `Code.gs`:
  - `?format=phase` → `{phase: 2}`
  - Setzen der Phase nur über `google.script.run.setPhase(n, adminToken)` aus dem Dashboard; nur sichtbar, wenn die Dashboard-URL `&admin=<ADMIN_TOKEN>` enthält. Der `ADMIN_TOKEN` steht im Tab `config`, nicht im Repo.
- `app.py`: fragt die Phase alle 10 s ab (Thread, ohne Blockade der UI) und entsperrt die Reiter bis einschließlich dieser Phase.
- **Fallback:** Liefert der Endpunkt 3 Mal hintereinander keine Antwort, werden **alle Reiter entsperrt** und eine dezente Meldung erscheint: „Freigabe offline – folgt einfach der Ansage vorne.“
- Bei Phase 0 ist nur „Start“ offen.

**Akzeptanz:** Tests für die Entsperrlogik (inkl. Fallback) mit gemocktem HTTP; Node-Test für `setPhase` mit falschem Token.

### AP6 (P1) – Dashboard für die neue Dramaturgie

**Ziel:** Das Dashboard am Beamer folgt den Phasen. Eine Person klickt sich durch; es gibt nichts zu suchen.

- **Kopfzeile:** große Phasen-Buttons `① Gutachten · ② LLM-Judge · ③ Paper vs. wir · ④ Challenge · Auflösung` sowie die Tastaturkürzel `1`–`5`. Jeder Button zeigt nur die zugehörigen Abschnitte an. Im Admin-Modus setzt derselbe Klick auch die Phase (AP5).
- **Statuszeile:** „Verbunden: Gruppe 1 ✅ · Gruppe 2 ✅ · Gruppe 3 ⏳ · Gruppe 4 ✅“ (Gruppen mit mindestens einem Record oder Join in der Session; dafür `join` im Sheet protokollieren, Tab `joins`).
- **Neue Ansichten:**
  1. **„Mensch: gleicher Code, andere Rolle“** (Phase ①): Balken mit Score je Gruppe, beschriftet mit „Rolle ?“. Ein Button „Rollen aufdecken“ ersetzt die Fragezeichen durch die Rollen.
  2. **„Mensch vs. LLM“** (Phase ②): Tabelle `bank_account` – Zeilen Mensch (je Rolle) und LLM je Modell × Haltung; Spalten Score und Recall.
  3. **„Paper vs. wir“** (Phase ③): links die Mittelwerte aus Chou (2026), Tabelle 6 (fest im Code hinterlegt: Gemini 4,66 / 7,28 / 7,99; DeepSeek 4,17 / 6,53 / 7,54; Kimi 4,29 / 6,69 / 7,20; Doubao 4,80 / 6,84 / 8,06), rechts unsere Ø-Scores je Modell × Haltung; darunter unsere Recall-Heatmap mit der Frage „Und der Recall?“. Quellenangabe unter der Grafik.
  4. **„Prognose vs. Ergebnis“** (Auflösung): Prognosen der Gruppen neben dem tatsächlichen Ergebnis (bester Judge nach Recall; Recall strict vs. lenient).
- **Vorhandene Ansichten neu einsortieren:** RQ2-Heatmaps → ②, Defekt-Matrix (RQ1) und RQ3-Kurve → ③ (eingeklappt als „Mehr“), Tests-Kontext, öffentlich vs. unbekannt, Formattreue → ③ „Mehr“, Leaderboard + Galerie → ④, Ground Truth → Auflösung.
- Die Prompt-Galerie zeigt pro Gruppe die **beste** Einreichung groß und lesbar (Schrift ≥ 18 px) – sie ist die Grundlage für die Abstimmung über die beste Erklärung.
- **Beamertauglich:** helles Theme, Schrift ≥ 18 px, keine horizontalen Scrollbalken bei 1280 × 720.

**Akzeptanz:** Node-Tests für die neue Aggregation (`human`-Records, Paper-Vergleich, Prognose vs. Ergebnis); `aggregate()` bleibt rückwärtskompatibel mit den bisherigen Feldern.

### AP7 (P2) – Gruppe 4: eigenes GPU-Notebook

**Ziel:** Gruppe 4 muss den Laufzeittyp nicht von Hand umstellen.

- `notebooks/hands_on_gpu.ipynb` = identisch zu `hands_on.ipynb`, aber in den Colab-Metadaten `"accelerator": "GPU"` und `"gpuType": "T4"`. Die Datei wird von `tools/build_notebooks.py` aus `hands_on.ipynb` erzeugt. Ein Test prüft, dass beide Notebooks bis auf die Metadaten gleich sind.
- Wenn die Gruppe den Code von Gruppe 4 eingibt, startet `app.py` **automatisch** im Hintergrund `ollama_colab.start_local_model()` und zeigt den Fortschritt im Reiter „Start“. Es gibt keine separate Ollama-Zelle mehr.
- Ohne GPU: automatische Umschaltung auf `local_fallback` mit Hinweis „Keine GPU verfügbar – ihr nutzt ein kleines Modell über OpenRouter“.
- README: zweiter Colab-Badge „Gruppe 4 (lokales Modell)“.

### AP8 (P1) – Doku, Aufräumen, Freeze

- `docs/RUNBOOK.md`: Minutenplan aus Abschnitt 1, Rollen (Eva: Setup, ②, ④ · Jessica: ①, Mini-Input, Betreuung · Alea: ③, Auflösung), Fallbacks um Gruppencode und Phasenfreigabe ergänzen.
- `docs/GUIDE_STUDENTS.md`: Inhalt aus **Abschnitt 5 (b)** dieses Dokuments übernehmen (eine Seite).
- `docs/GUIDE_INSTRUCTOR.md`: Inhalt aus **Abschnitt 4 (a)** übernehmen (Testplan als Checkliste) + Gruppencodes + Admin-Link.
- `docs/CONCEPT.md`: Ablauf und Methoden auf 75 min aktualisieren; Vernissage durch „Prompt-Galerie als Teil der AI Challenge“ ersetzen (Vernissage steht nicht im Methodenpool).
- `README.md`: OneDrive-Link und Team-To-dos entfernen (vor der Veröffentlichung des Repos), beide Colab-Badges.
- `NOTEBOOK_VERSION` hochzählen.
- Am 17.11.: `DEFAULT_SESSION_ID = "2026-11-19-live"`, Tag `v1.0-session`.

---

## 4. (a) Testplan für Eva – was du noch testen musst

Abhaken in dieser Reihenfolge. Zielwerte stehen in Klammern. Was rot ist, geht als Bug an Claude Code.

### A. Lokal (nach jedem Arbeitspaket, ca. 2 min)

- [ ] `uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -e ".[dev]"`
- [ ] `.venv/bin/python -m pytest` → alles grün
- [ ] `node --test scoreboard/aggregate.test.mjs` → alles grün
- [ ] `git grep -n "sk-or-"` → kein Treffer

### B. Scoreboard neu deployen (einmal nach AP2/AP5/AP6)

- [ ] `Code.gs` und `dashboard.html` ins Apps-Script-Projekt kopieren.
- [ ] **Bereitstellungen verwalten → Bearbeiten → Version: „Neue Version“** (nicht „Neue Bereitstellung“, sonst ändert sich die URL).
- [ ] Sheet-Tabs vorhanden: `runs`, `config` (`session_id`, `phase`, `admin_token`), `keys`, `joins`.
- [ ] Tab `keys`: 4 Codes + Keys eingetragen, `active = TRUE`.
- [ ] Im Browser: `…/exec?action=join&code=<Code>&token=<Token>` liefert Gruppe + Key; ein falscher Code liefert die Fehlermeldung.
- [ ] `…/exec?format=phase` liefert die Phase.

### C. Studierenden-Sicht (Inkognito-Fenster, **anderes** Google-Konto als deins)

- [ ] README-Badge → Colab öffnet `hands_on.ipynb`, ohne Login bei GitHub (Repo öffentlich?).
- [ ] ▶ Start → Warndialog „Trotzdem ausführen“ erscheint → danach Oberfläche in **< 2 min**.
- [ ] Code eintippen (auch klein geschrieben, mit Leerzeichen) → „✅ Ihr seid Gruppe …“.
- [ ] Falscher Code → verständliche Meldung, kein Traceback.
- [ ] Reiter 1–5 gesperrt, solange die Phase 0 ist.
- [ ] Zelle ein zweites Mal ausführen → Zustand bleibt, kein Neu-Download.

### D. Ablauf einmal komplett im Probemodus (Mock, kostenlos)

Admin-Dashboard parallel offen (`…/exec?admin=<Token>`), Phasen nacheinander schalten:

- [ ] Phase 1 → Reiter „1 Gutachten“ entsperrt sich innerhalb von **≤ 10 s**.
- [ ] Gutachten abgeben (z. B. `26, 31`) → „x von 6 gefunden“, **keine Zeilen sichtbar**; Dashboard ① zeigt den Balken, „Rollen aufdecken“ funktioniert.
- [ ] Phase 2 → Prognose absenden → Dashboard zeigt sie; „Unseren Judge bewerten lassen“ → Vergleichstabelle Mensch vs. LLM.
- [ ] Schritt 3 starten → läuft im Hintergrund weiter, während du den Reiter wechselst.
- [ ] Phase 3 → Dashboard „Paper vs. wir“ zeigt Paper-Werte und eure Werte.
- [ ] Phase 4 → Probelauf, 3 Einreichungen, 4. Einreichung wird gesperrt; Leaderboard und Galerie aktualisieren sich.
- [ ] Auflösung → Ground Truth und „Prognose vs. Ergebnis“ erscheinen.

### E. Echte Modelle (Generalprobe 1, mit Jessica und Alea, 4 Geräte gleichzeitig)

| Messpunkt | Zielwert | Ist |
|---|---|---|
| Start bis „✅ Ihr seid Gruppe …“ | < 2 min | |
| Schritt 2 (3 Läufe) je API-Gruppe | < 1 min | |
| Schritt 3 (15 Läufe) je API-Gruppe | < 4 min | |
| Gruppe 4: GPU-Notebook → Modell bereit | < 5 min | |
| Gruppe 4: Schritt 2 + 3 (2 + 10 Läufe) | < 10 min | |
| Einreichung Challenge (6 + 6 Läufe) | < 2 min | |
| Anteil `parse_ok = False` je Modell | ≈ 0 | |
| Kosten pro Gruppe (Instructor-Notebook „Kosten“) | < 1 $ | |
| Dashboard-Aktualisierung | ≤ 10 s | |

- [ ] Modell-IDs in `config.py` gegen `openrouter.ai/api/v1/models` geprüft (Reasoning-Modelle: auf `parse_ok` achten).
- [ ] Gruppe 4 ohne GPU simulieren (normales Notebook statt GPU-Notebook) → automatischer Fallback.
- [ ] Liegt Gruppe 4 über den Zielwerten: Schritt 3 lokal auf 5 Läufe (nur strict) reduzieren.

### F. Fallbacks (je 1 Minute)

- [ ] `SCOREBOARD_URL` testweise falsch → Läufe landen in `/content/scoreboard_backup.csv`; „Erweitert“ klappt beim Start auf.
- [ ] Phasen-Endpunkt nicht erreichbar → nach ca. 30 s alle Reiter offen + Hinweis.
- [ ] Mock-Modus über „Erweitert“ → Läufe landen in `<session>-mock`, nicht im Leaderboard.
- [ ] Dashboard: Schalter „Vorab-Daten einblenden“ zeigt die `precomputed`-Läufe.

### G. Beamer und Raum

- [ ] Dashboard in 1280 × 720 ohne horizontales Scrollen, Schrift aus der letzten Reihe lesbar.
- [ ] WLAN im Raum mit Colab getestet (oder Hotspot bereit).
- [ ] Notfall-Folie mit Screenshot der Vorab-Daten und den 4 Gruppen + Keys (nur für den Fallback).

### H. Am Vortag (16./17.11.)

- [ ] `DEFAULT_SESSION_ID = "2026-11-19-live"` + gleicher Wert im Sheet; gepusht.
- [ ] Phase im Sheet auf `0`.
- [ ] Vorab-Läufe (`precomputed`) und Baseline-Prompt mit dem Instructor-Notebook erzeugt.
- [ ] Repo öffentlich, README ohne OneDrive-Link, Tag `v1.0-session`.
- [ ] Gruppencodes auf der Setup-Folie = Codes im Sheet.

---

## 5. (b) So legen die Studierenden los (Vorlage für `GUIDE_STUDENTS.md` und die Setup-Folie)

**Ihr braucht:** einen Laptop pro Zweiergruppe und ein Google-Konto. Installieren müsst ihr nichts.

1. **QR-Code scannen** oder Link öffnen. Gruppe 4 nutzt den **zweiten** QR-Code (Notebook mit Grafikkarte).
2. Colab öffnet sich. Oben rechts ggf. **„Anmelden“** mit eurem Google-Konto.
3. Auf **▶** neben „Start – hier klicken“ klicken.
4. Colab fragt: *„Dieses Notebook wurde nicht von Google erstellt.“* → **„Trotzdem ausführen“**.
5. Nach ca. 1 Minute erscheint die Oberfläche. **Gruppencode von der Folie** eintippen → **„Los geht's“**.
   Ihr seht: „✅ Ihr seid Gruppe X – euer Judge heißt …“. Gruppe 4: Das lokale Modell lädt jetzt im Hintergrund, einfach weitermachen.
6. Ab jetzt nur noch die **Reiter von links nach rechts**. Gesperrte Reiter (🔒) öffnen sich, wenn wir vorne das Signal geben.

| Reiter | Was ihr tut | Dauer |
|---|---|---|
| **1 Gutachten** | Rollenkarte lesen (**nicht verraten!**), Code lesen, Fehlerzeilen eintragen, Score 1–10 geben, ein Satz Begründung → „Gutachten abgeben“ | 5 min |
| **2 LLM-Judge** | Prognose abgeben → „Unseren Judge bewerten lassen“ → eure Bewertung mit der des LLM vergleichen (3 Leitfragen) | 8 min |
| **3 Alle Beispiele** | „Restliche Beispiele starten“ – läuft im Hintergrund weiter, ihr könnt zuhören | 1 Klick |
| **4 Challenge** | Eigenen Judge-Prompt schreiben, beliebig oft auf einem Beispiel testen, **maximal 3 Mal einreichen**. +2 Punkte pro echtem Fehler, −1 pro Fehlalarm. Keine Hinweise auf bestimmte Zeilen oder Funktionen. | 20 min |
| **5 Abschluss** | Umfrage-Link öffnen, abstimmen | 1 min |

**Wenn etwas hakt:** Gelbe ⚠️-Meldungen sagen, was fehlt. Sonst Hand heben. Den Code in der Zelle müsst ihr weder lesen noch ändern.
**Datenschutz:** An die KI-Anbieter gehen nur der Beispielcode und euer Prompt. Gespeichert werden Gruppennummer, Ergebnisse und eingereichte Prompts, keine Namen.

---

## 6. Hinweise für Claude Code

- Vor dem Start `docs/CONCEPT.md`, `docs/RUNBOOK.md`, `judge_lab/ui.py`, `judge_lab/runner.py`, `scoreboard/Code.gs` und `scoreboard/dashboard.html` lesen.
- Testgetrieben arbeiten, besonders bei `human.parse_lines`, der Stufenlogik und der Freigabelogik.
- Pro Arbeitspaket ein Commit; Commit-Nachricht nennt das AP.
- Nach AP6 einen Screenshot des Dashboards in 1280 × 720 erzeugen (z. B. mit einer statischen HTML-Vorschau und Mock-Daten), damit Eva das Layout prüfen kann, ohne neu zu deployen.
- Bei Unklarheiten zu Didaktik oder Ablauf: nicht raten, sondern in `docs/plans/OFFENE_FRAGEN.md` notieren und weitermachen.
