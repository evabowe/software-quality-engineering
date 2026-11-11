# Leitfaden für Lehrende: Vorbereitung und Betrieb

Für Eva, Jessica und Alea. Ablauf am Tag selbst: [RUNBOOK.md](RUNBOOK.md). Hintergrund und Abweichungen: [CONCEPT.md](CONCEPT.md).

## 1. Lokale Entwicklung

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/python -m pytest          # gesamte Suite inkl. Ground-Truth-Prüfung und Node-Tests (~20–40 s)
```

Auf macOS kann es passieren, dass Python das Editable-Install ignoriert (`ModuleNotFoundError: judge_lab` außerhalb von pytest). Ursache sind als „hidden“ markierte `.pth`-Dateien; Abhilfe: `chflags nohidden .venv/lib/python3.12/site-packages/*.pth`.

Wichtige Befehle:

| Zweck | Befehl |
|---|---|
| QuixBugs-Snippets neu übernehmen | `python tools/import_quixbugs.py <QuixBugs-Checkout> bitcount quicksort levenshtein shunting_yard next_permutation` |
| Komplexität neu messen | `python tools/compute_complexity.py` |
| Nur die Scoreboard-Aggregation testen | `node --test scoreboard/aggregate.test.mjs` |
| Prompt-Snapshot bewusst erneuern | `tests/snapshots/*.txt` löschen, pytest laufen lassen, Diff prüfen, committen |

## 2. Checkliste vor der Generalprobe

1. **Modell-IDs prüfen** (spätestens eine Woche vorher) und in `judge_lab/config.py` fixieren:
   ```bash
   curl -s https://openrouter.ai/api/v1/models | python -c "import json,sys; [print(m['id']) for m in json.load(sys.stdin)['data'] if any(k in m['id'] for k in ('gemini','deepseek','kimi','qwen'))]"
   ```
   Achtung bei Reasoning-Modellen: Sie verbrauchen einen Teil von `MAX_TOKENS = 2000` fürs Denken. Wenn in der Generalprobe viele Läufe eines Modells `parse_ok = False` haben, ist das die wahrscheinliche Ursache (Modell tauschen oder `MAX_TOKENS` erhöhen).
2. **Ollama-Tag prüfen** auf ollama.com (`qwen2.5-coder:3b`; 7B nur, wenn Download und Inferenz in der Probe schnell genug sind).
3. **Scoreboard deployen**: [scoreboard/DEPLOY.md](../scoreboard/DEPLOY.md). Danach `SCOREBOARD_URL` und `SCOREBOARD_TOKEN` in `config.py` eintragen.
4. **Session-ID setzen**: `DEFAULT_SESSION_ID` in `config.py` (z. B. `rehearsal-1`, am Tag `2026-11-19-live`) und dieselbe ID im Sheet-Tab `config` als `session_id`. Die Notebooks klonen den Stand von `main`; die Änderung muss also gepusht sein.
5. **`NOTEBOOK_VERSION`** in `judge_lab/__init__.py` bei jeder Änderung hochzählen; auf dem Scoreboard fallen veraltete Kopien dann auf.
6. **Repo öffentlich machen** (sonst funktionieren Klon und Colab-Badge nicht ohne Login). Vorher den OneDrive-Link aus der README entfernen.
7. **Instructor-Notebook** ausführen: Ground Truth hochladen, Mock-Durchlauf (Session `ci`) → Dashboard unter `…/exec?session=ci` prüfen.

## 3. API-Keys (OpenRouter)

- Pro Gruppe **ein eigener Key** mit Kreditlimit (z. B. 2 $), dazu ein Instructor-Key. Anlegen unter openrouter.ai → Keys.
- Gruppe 4 braucht ebenfalls einen Key: Ihre Einreichungen laufen zusätzlich auf dem Referenzmodell, und der Fallback ohne GPU läuft über OpenRouter.
- Verteilung am Tag über **Gruppencodes** (siehe unten), **nie im Repo**; Keys im Klartext nur auf der Notfall-Folie. Ein Test prüft, dass keine `sk-or-…`-Keys in den Notebooks stehen.
- In Colab können Gruppen den Key alternativ als Secret `OPENROUTER_API_KEY` hinterlegen; das Setup liest ihn dann automatisch.
- **Nach der Session alle Keys widerrufen.**
- Verbrauch prüfen: Instructor-Notebook, Zelle „Kosten“.

Kostenschätzung (Konzept 11): 2–3 Mio. Tokens, je nach Modell ca. 1–8 €.

### Gruppencodes anlegen

Die Studierenden tippen nur einen kurzen Code von der Folie ab; Gruppe und Key liefert die Scoreboard-Web-App (`?action=join`).

1. Im Sheet einen Tab `keys` mit der Kopfzeile `code | group | openrouter_key | active` anlegen.
2. Pro Gruppe eine Zeile, z. B. `K7Q2 | Gruppe 2 | sk-or-… | TRUE`. Die Gruppe muss genau so heißen wie in `config.py` (`Gruppe 1` … `Gruppe 4`).
3. **Codes:** 4 Zeichen aus `ABCDEFGHJKLMNPQRSTUVWXYZ23456789` (ohne die verwechselbaren 0/O und 1/I). Erzeugen z. B. mit
   `python -c "import secrets; a='ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; print([''.join(secrets.choice(a) for _ in range(4)) for _ in range(4)])"`.
   Groß/klein und Leerzeichen spielen beim Eintippen keine Rolle.
4. **Pro Session neue Codes** (Generalprobe ≠ Live-Session). Codes auf der Setup-Folie = Codes im Sheet.
5. Das Sheet bleibt **privat**; nur die Web-App (läuft als „Ich“) liest den Tab. Der Endpunkt verlangt das `token` aus dem Tab `config`.
   Da dieses Token im Repo steht, schützt es nur vor Zufallstreffern: Keys deshalb immer mit Kreditlimit anlegen.
6. **Nach der Session:** alle Keys bei OpenRouter widerrufen und den Tab `keys` leeren (oder `active = FALSE`).

Test im Browser: `…/exec?action=join&code=<Code>&token=<Token>` liefert `{"status":"ok","group":…,"key":…}`, ein falscher Code `{"status":"error","message":"Code unbekannt"}`.

Ist der Code-Server nicht erreichbar, klappt im Reiter „Start“ der Bereich **Erweitert** auf: Dort tragen die Gruppen Gruppe und Key von der Notfall-Folie ein (wie bisher).

## 4. Lokales Modell (Gruppe 4)

- Gruppe 4 öffnet **`hands_on_gpu.ipynb`** (zweiter QR-Code / zweiter Badge in der README). Das Notebook fordert in Colab automatisch eine **T4-GPU** an; den Laufzeittyp muss niemand umstellen. Erzeugt wird es mit `python tools/build_notebooks.py` aus `hands_on.ipynb` – nach jeder Änderung an `hands_on.ipynb` erneut ausführen (ein Test prüft das).
- Sobald Gruppe 4 ihren Code eingibt, startet das Notebook Ollama **im Hintergrund** (installieren, Server, Modell laden, Testanfrage) und zeigt den Fortschritt im Reiter „Start“.
- **Ohne GPU** schaltet es sofort auf das kleine Modell über OpenRouter um („Keine GPU verfügbar – ihr nutzt ein kleines Modell über OpenRouter“). Gruppe 4 braucht deshalb ebenfalls einen Key im Tab `keys`.
- Das lokale Modell läuft reduziert: Haltungen strict + lenient (`LOCAL_ATTITUDES`), keine Läufe mit Tests. Schritt 2 = 2 Läufe, Schritt 3 = 10 Läufe. Ist das zu langsam: `LOCAL_ATTITUDES = ("strict",)` → 1 + 5 Läufe.

## 5. Freigabe, Admin-Link und Testplan

**Admin-Link:** `…/exec?admin=<admin_token>` (Token aus dem Sheet-Tab `config`, nicht im Repo). Nur damit erscheint der gelbe Kasten mit den Phasen 0–5, und nur damit setzen die Ansichts-Buttons die Freigabe im Notebook mit. Ohne `admin` ist das Dashboard reine Anzeige (z. B. für einen zweiten Bildschirm).

**Testplan** (Reihenfolge einhalten; Zielwerte in Klammern):

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

## 6. Offene Abstimmungen im Team

Didaktische und inhaltliche Fragen aus dem Umbau: [plans/OFFENE_FRAGEN.md](plans/OFFENE_FRAGEN.md).


- Toleranzbereiche der bank_account-Defekte (siehe CONCEPT.md 5.2) und Tippfehler „Überisung“ (Z. 38) mit Jessica klären.
- Wertungslücke bei `style`-Befunden in der Challenge (CONCEPT.md 5.4): Regel lassen und bei der Prompt-Galerie offenlegen, oder neutrale Befunde abwerten?
- Rechteinhaber in `LICENSE` (derzeit Eva Bowe) bestätigen.
