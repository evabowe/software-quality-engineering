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
- Verteilung am Tag über die Folie/QR-Code, **nie im Repo**. Ein Test prüft, dass keine `sk-or-…`-Keys in den Notebooks stehen.
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

- Colab: Laufzeit → Laufzeittyp ändern → **T4-GPU**. Die Zelle „🖥️ Nur Gruppe 4“ installiert Ollama, startet den Server, lädt das Modell und schickt eine Testanfrage. Mehrfaches Ausführen schadet nicht.
- Ohne GPU meldet die Zelle das. Dann im Setup „Gruppe 4 ohne GPU“ ankreuzen: Die Gruppe nutzt ein kleines Modell über OpenRouter, die Bedingung „kleines Modell“ bleibt erhalten.
- Auftrag 1 läuft für das lokale Modell reduziert: 6 Snippets × {strict, lenient} × ohne Tests = 12 Läufe.

## 5. Generalprobe: was messen?

| Messpunkt | Zielwert | Notiz |
|---|---|---|
| Setup-Zeit bis „✅ Bereit“ | < 2 min | |
| Dauer Auftrag 1 je API-Gruppe (36 Läufe) | < 5 min | |
| Ollama: Download + erste Antwort | < 5 min | |
| Dauer Auftrag 1 lokal (12 Läufe) | < 8 min | sonst auf 6 Läufe kürzen (`assignment1_variants`) |
| Anteil `parse_ok = False` je Modell | möglichst 0 | Dashboard „Formattreue“ |
| Kosten pro Gruppe | < 1 $ | Zelle „Kosten“ |
| Dashboard-Aktualisierung | ≤ 10 s | |

Danach: Vorab-Läufe (`precomputed`) mit dem Instructor-Notebook erzeugen; sie dienen als Fallback im Dashboard.

## 6. Offene Abstimmungen im Team

- Toleranzbereiche der bank_account-Defekte (siehe CONCEPT.md 5.2) und Tippfehler „Überisung“ (Z. 38) mit Jessica klären.
- Wertungslücke bei `style`-Befunden in der Challenge (CONCEPT.md 5.4): Regel lassen und in der Vernissage offenlegen, oder neutrale Befunde abwerten?
- Rechteinhaber in `LICENSE` (derzeit Eva Bowe) bestätigen.
