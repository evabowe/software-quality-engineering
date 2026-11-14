# Dashboard einrichten und testen

Das Dashboard ist eine Apps-Script-Web-App an einem privaten Google Sheet. `sende` schickt die Ergebnisse per POST, und das Dashboard lädt alle 10 Sekunden neu.

## 1. Sheet vorbereiten

- **Tab `config`:** Spalte A ist der Schlüssel, Spalte B der Wert.

  | A | B |
  |---|---|
  | `token` | muss gleich `SCOREBOARD_TOKEN` in `judge_lab/config.py` sein |
  | `session_id` | aktive Session, z. B. `probe-1`; das Dashboard zeigt nur diese |

  Die alten Zeilen `phase` und `admin_token` werden nicht mehr gebraucht und können gelöscht werden.
- **Tab `keys`:** Kopfzeile `code | group | openrouter_key | active`, eine Zeile pro Gruppe, z. B. `K7QX | Gruppe 2 | sk-or-… | TRUE`.
  - Die Reihenfolge der Zeilen bestimmt die Reihenfolge der Kacheln. Der Gruppenname ist frei wählbar.
  - Codes: 4 Zeichen ohne 0/O/1/I, z. B. erzeugt mit `python -c "import secrets; a='ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; print([''.join(secrets.choice(a) for _ in range(4)) for _ in range(4)])"`.
  - Pro Session neue Codes. Keys bei OpenRouter immer mit Kreditlimit anlegen (das Token steht im öffentlichen Repo). Nach der Session alle Keys widerrufen.
- **Alter Tab `runs`** (vom vorigen Setup, 34 Spalten): **in `runs_alt` umbenennen.** Das Skript legt `runs` mit der neuen Kopfzeile neu an. Einen Tab mit fremder Kopfzeile lehnt es ab („alte Kopfzeile – bitte in runs_alt umbenennen“), und `sende` sichert dann nur lokal.
- Die Tabs `defects` und `joins` aus dem alten Setup können bleiben. `joins` wird weiter genutzt.

## 2. Skript deployen

1. Im Sheet **Erweiterungen → Apps Script** öffnen.
2. `Code.gs` durch den Inhalt von `scoreboard/Code.gs` ersetzen und die HTML-Datei `dashboard` durch `scoreboard/dashboard.html`.
3. Speichern, dann **Bereitstellen → Bereitstellungen verwalten → Bearbeiten → Version: Neue Version → Bereitstellen.** Die URL bleibt gleich. Ohne neue Version läuft unter der URL weiter der alte Stand.
4. Nur bei einer *neuen* Bereitstellung ändert sich die URL. Dann `SCOREBOARD_URL` in `judge_lab/config.py` anpassen, mit *Ausführen als: Ich* und *Zugriff: Jeder*.

**Schnelltest im Terminal** (im Repo-Ordner; `URL` und `TOKEN` kommen aus `config.py`):

```bash
URL=$(.venv/bin/python -c "from judge_lab.config import SCOREBOARD_URL as u; print(u)")
TOKEN=$(.venv/bin/python -c "from judge_lab.config import SCOREBOARD_TOKEN as t; print(t)")
curl -L "$URL" -H "Content-Type: application/json" -d '{"token":"'$TOKEN'","records":[{"timestamp":"2026-11-14T10:00:00+00:00","run_id":"curl-1","gruppe":"Gruppe 1","runde":1,"snippet":"bank_account","modell":"curl","prompt":"Test","code_score":5,"judge_score":2,"einreichung":"curl"}]}'
# → {"status":"ok","records":1}
curl -L "$URL?format=json"                                   # → aggregierte Kacheln
curl -L "$URL?action=join&code=<CODE>&token=$TOKEN"          # → {"status":"ok","group":…,"key":…}
```

## 3. Durchlauf mit dem Test-Notebook

`notebooks/eva_test.ipynb` liegt nur lokal und wird nicht committet. Es läuft gegen den lokalen Checkout.

1. Im Tab `config` `session_id` auf einen Probenwert setzen (z. B. `probe-1`) und das Dashboard (Web-App-URL) im Browser öffnen.
2. Im Notebook einen echten Code aus dem Tab `keys` in `verbinde("…")` eintragen und alle Zellen ausführen.
3. Am Dashboard prüfen:
   - [ ] Nach `verbinde` zeigt die Kachel der Gruppe „verbunden – noch nichts gesendet“.
   - [ ] **Taste 1:** Die Kachel zeigt Judge-Score, Code-Score und Prompt, darunter `bank_account · openai/gpt-6-luna · gerade eben`.
   - [ ] **Taste 2:** Die Kachel zeigt den *zweiten* Rollen-Prompt (der zuletzt gesendete gewinnt).
   - [ ] **Taste 3:** Die Kachel zeigt ein Diagramm mit L1–L5, blau für den Code-Score (links), orange für den Judge-Score (rechts).
   - [ ] **Taste 4:** Die Kachel zeigt Summe und Durchschnitt, „5/5 Snippets“ und ist als 🏆 vorne hervorgehoben (einzige Gruppe).
   - [ ] Ein Klick auf einen Prompt klappt den vollen Text auf.
   - [ ] Im Tab `runs` ist `code_score` eine Zahl (z. B. `5,2`, kein Datum), `timestamp` und `prompt` stehen als Text ohne sichtbares `'`.
   - [ ] Die Zelle von Runde 4 noch einmal ausführen: Die Kachel zeigt weiter „5/5 Snippets“ und dieselbe Summe.
4. **Offline-Probe:** In `config.py` `SCOREBOARD_URL = ""` setzen, Kernel neu starten und `sende` ausführen. Erwartet wird „lokal gesichert“, und `scoreboard_backup.csv` liegt im Arbeitsverzeichnis. URL zurücksetzen, Kernel neu starten und noch einmal `sende` ausführen. Die gesicherten Zeilen erscheinen dann mit am Dashboard, und die CSV ist weg.
5. Danach `session_id` auf die Live-Session setzen (z. B. `2026-11-19-live`). Das Dashboard ist dann leer.

## 4. Layout ohne Deployment prüfen

```bash
node tools/dashboard_preview.mjs /tmp/preview   # schreibt runde-1.html … runde-4.html mit Beispieldaten
open /tmp/preview/runde-3.html
```

## 5. Tests

```bash
.venv/bin/python -m pytest -q                  # Python + Vertrag Python ↔ Code.gs
node --test scoreboard/aggregate.test.mjs      # Aggregation der Kacheln
```
