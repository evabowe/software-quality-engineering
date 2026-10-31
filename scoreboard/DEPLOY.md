# Scoreboard deployen (Google Apps Script)

Das Scoreboard ist eine Apps-Script-Web-App an einem Google Sheet. Die Notebooks senden jeden Lauf per POST; das Dashboard liest die aggregierten Daten alle 10 Sekunden. Dauer: etwa 15 Minuten.

## 1. Sheet anlegen

1. Neues Google Sheet anlegen, z. B. „Scoreboard LLM-as-a-Judge 2026-11-19“.
2. Tab `config` anlegen und zwei Zeilen eintragen (Spalte A = Schlüssel, Spalte B = Wert):

   | A | B |
   |---|---|
   | `token` | eine zufällige Zeichenkette, z. B. aus `python -c "import secrets; print(secrets.token_urlsafe(16))"` |
   | `session_id` | aktive Session, z. B. `rehearsal-1` oder `2026-11-19-live` |

   Die Tabs `runs` und `defects` legt das Skript selbst an.

## 2. Skript einfügen

1. Im Sheet: **Erweiterungen → Apps Script**.
2. Den Inhalt von `Code.gs` aus diesem Ordner in die Datei `Code.gs` des Projekts kopieren (vorhandenen Inhalt ersetzen).
3. **Datei hinzufügen (+) → HTML**, Name `dashboard` (ohne Endung), Inhalt von `dashboard.html` einfügen.
4. Speichern.

## 3. Als Web-App bereitstellen

1. **Bereitstellen → Neue Bereitstellung → Typ: Web-App**.
2. *Ausführen als:* **Ich**. *Zugriff:* **Jeder** (die Studierenden haben kein Google-Login im Notebook).
3. Beim ersten Mal die Berechtigungen bestätigen (Zugriff auf das eigene Sheet).
4. Die angezeigte **Web-App-URL** (endet auf `/exec`) kopieren.

Wichtig: Nach jeder Änderung am Skript **Bereitstellungen verwalten → Bearbeiten → Version: Neue Version**. Sonst läuft unter der URL weiter der alte Stand.

## 4. Testen

POST mit einem Beispiel-Lauf (fehlende Felder bleiben leer):

```bash
URL="https://script.google.com/macros/s/…/exec"
curl -L -X POST "$URL" -H "Content-Type: application/json" -d '{
  "token": "DEIN-TOKEN",
  "record": {"timestamp": "2026-11-08T10:00:00+00:00", "session_id": "deploy-test", "group": "Gruppe 1",
             "phase": "a1", "model_key": "mock", "model_id": "mock", "attitude": "objective",
             "snippet_id": "qb_quicksort", "complexity_level": "L2", "with_tests": false,
             "tp": 1, "fp": 1, "neutral": 1, "n_defects": 1, "recall": 1.0, "precision": 0.5,
             "weighted_score": 5.0, "found_defect_ids": "D1", "parse_ok": true, "notebook_version": "0.1.0"}
}'
```

Erwartete Antwort: `{"status":"ok"}`, und im Tab `runs` steht eine neue Zeile. Mit falschem Token: `{"status":"error","message":"Ungültiges Token"}`.

Aggregierte Daten abrufen:

```bash
curl -L "$URL?format=json&session=deploy-test"
```

Das Dashboard öffnet sich unter der URL ohne Parameter im Browser; eine andere Session zeigt `…/exec?session=rehearsal-1`.

## 5. In das Paket eintragen

In `judge_lab/config.py`:

```python
SCOREBOARD_URL = "https://script.google.com/macros/s/…/exec"
SCOREBOARD_TOKEN = "DEIN-TOKEN"
```

Der Token ist kein echtes Geheimnis (er steht im öffentlichen Repo), verhindert aber zufällige Posts.

## 6. Ground Truth hochladen

Für die Defekt-Matrix (RQ1) und die Auflösung braucht das Dashboard die Liste aller Defekte. Im Instructor-Notebook die Zelle „Ground Truth ans Scoreboard senden“ ausführen; sie füllt den Tab `defects`. Die Auflösung bleibt im Dashboard verborgen, bis jemand auf „Ground Truth anzeigen“ klickt.

## 7. Mock-Durchlauf

Im Instructor-Notebook eine Matrix mit dem Modell `mock` und `session_id = "ci"` laufen lassen. Danach muss das Dashboard unter `…/exec?session=ci` alle Ansichten füllen (Recall-Werte des Mocks sind bedeutungslos).

## Fallback ohne Web-App

Ist das Scoreboard nicht erreichbar, schreibt jedes Notebook die Läufe nach `/content/scoreboard_backup.csv`. Diese Datei kann über das Instructor-Notebook („Sicherung nachsenden“) eingespielt oder direkt in den Tab `runs` importiert werden (Kopfzeile identisch).
