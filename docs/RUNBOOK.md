# Runbook für den 19.11.2026 (75 min interaktiv)

Vorbereitung und Testplan: [GUIDE_INSTRUCTOR.md](GUIDE_INSTRUCTOR.md). Hintergrund: [CONCEPT.md](CONCEPT.md).
Rollen: **Eva** Setup, ② LLM-Judge, ④ Challenge · **Jessica** ① Gutachten, Mini-Input, Betreuung · **Alea** ③ Paper vs. wir, Auflösung.

## Am Vortag

- [ ] `DEFAULT_SESSION_ID = "2026-11-19-live"` in `judge_lab/config.py`, gleicher Wert im Sheet-Tab `config`; gepusht.
- [ ] Im Sheet-Tab `config`: `phase = 0`, `admin_token` gesetzt (nicht im Repo).
- [ ] Tab `keys`: 4 neue Gruppencodes + Keys, `active = TRUE`. Codes auf der Setup-Folie = Codes im Sheet.
- [ ] Modell-IDs fixiert, Generalprobe bestanden, Vorab-Läufe (`precomputed`) im Sheet, Ground Truth hochgeladen.
- [ ] Folien: Setup-Folie mit zwei QR-Codes (Gruppen 1–3: `hands_on.ipynb`, Gruppe 4: `hands_on_gpu.ipynb`) und den Gruppencodes; **Notfall-Folie** mit Gruppen + Keys und Screenshot der Vorab-Daten.
- [ ] Rollenkarten-Zuordnung geprüft (`HUMAN_ROLES` in `config.py`: Gruppe 1 strict, 2 objective, 3 lenient, 4 ohne Rolle).

## 15 Minuten vorher

- [ ] Dashboard am Beamer im **Admin-Modus**: `…/exec?admin=<admin_token>`. Session prüfen, „Vorab-Daten“ **aus**, Phase steht auf 0.
- [ ] Instructor-Notebook in Colab geöffnet.
- [ ] Eigener Laptop: Notebook im Probemodus (Erweitert → Probemodus) einmal durchklicken.

## Minutenplan

Das Dashboard hat oben die Ansichten **① Gutachten · ② LLM-Judge · ③ Paper vs. wir · ④ Challenge · Auflösung** (Tasten 1–5). Im Admin-Modus schaltet derselbe Klick die Reiter im Notebook frei (nie zurück): ① → Reiter 1, ② → Reiter 2 **und 3**, ③ → wie ②, ④ → Reiter 4, Auflösung → Reiter 5. Die Zahlen 0–5 im gelben Kasten setzen die Phase direkt.

| Min. | Phase | Dashboard | Was passiert | Wer |
|---|---|---|---|---|
| 0–5 | Ankommen, Setup, Vorher-Umfrage (Menti) | Statuszeile „Verbunden“ | QR-Code, ▶ Start, „Trotzdem ausführen“, Gruppencode eintippen. Warten, bis 4 × ✅. | Eva |
| 5–15 | ① Ihr seid der Judge (**Gutachten erstellen**) | ① | Rollenkarte lesen (nicht verraten!), `bank_account` bewerten: Zeilen, Score, ein Satz. Danach Balken besprechen, **„Rollen aufdecken“**. | Jessica |
| 15–20 | Mini-Input LLM-as-a-Judge | – | Folien | Jessica |
| 20–32 | ② Gleicher Code, LLM als Judge | ② | Prognose absenden → „Unseren Judge bewerten lassen“ → Vergleichstabelle + 3 Leitfragen → „Restliche Beispiele starten“ (läuft im Hintergrund). | Eva |
| 32–44 | ③ Paper vs. wir, Kritik (Heißer Stuhl optional) | ③ | Paper-Scores neben unseren, dann „Und der Recall?“. Mehr-Bereich nur bei Zeit. | Alea |
| 44–64 | ④ Prompt-Challenge (**AI Challenge**) | ④ | Probeläufe, max. 3 Einreichungen. Leaderboard live; zum Schluss Prompt-Galerie: Gewinnergruppe erklärt, Plenum stimmt ab. | Eva, Jessica betreut |
| 64–70 | Auflösung, Prognose-Check, Nachher-Umfrage | Auflösung | Prognose vs. Ergebnis, „Ground Truth anzeigen“, Umfrage. | Alea |
| 70–75 | Blitzlicht + Ausblick | – | „Würde ich einen LLM-Judge in die CI einbauen – unter welcher Bedingung?“ | alle |

**Zeitpuffer:** Wird es knapp, wird die Challenge auf 2 Einreichungen gekürzt (mündlich ansagen). Die Auflösung wird nicht gekürzt.

### Moderationsthesen (nicht vorab verraten)

- Gleicher Code, andere Rolle: Die Scores der Gruppen streuen mit der Rolle – wie beim LLM (RQ2).
- „strict“ senkt den Score deutlich, erhöht den Recall aber kaum → *Strenge ≠ Gründlichkeit*.
- „strict“ erzeugt mehr Fehlalarme (der Paper-Prompt verlangt mindestens drei Mängel) → Strenge kostet Präzision.
- Testkontext hilft bei `quicksort`/`bank_account`, weil Testnamen die Absicht verraten (Bonus in Schritt 3).
- `shunting_yard` (fehlende Zeile) wird seltener gefunden.
- Kleines lokales Modell: weniger Recall, mehr unlesbare Antworten → Datenschutz vs. Qualität.
- QuixBugs ist öffentlich, bank_account nicht: Ist ein höherer Recall bei QuixBugs Können oder Erinnern?

## Fallbacks

| Problem | Erkennbar an | Sofortmaßnahme |
|---|---|---|
| Code-Server nicht erreichbar | Im Reiter „Start“ klappt „Erweitert“ auf: „Code-Server nicht erreichbar …“ | Notfall-Folie zeigen: Gruppen tragen unter „Erweitert“ Gruppe + Key ein und klicken „Speichern“. |
| Falscher Code | „Code unbekannt“ | Code von der Folie noch einmal abtippen (Groß/klein und Leerzeichen egal); Sheet-Tab `keys` prüfen (`active = TRUE`). |
| Phasenfreigabe hängt | Reiter bleiben 🔒, obwohl die Phase gesetzt ist | Nach ca. 30 s ohne Antwort öffnen sich alle Reiter von selbst („Freigabe offline – folgt einfach der Ansage vorne“). Sonst Phase im Sheet-Tab `config` von Hand setzen. |
| Keine T4-GPU für Gruppe 4 | „Keine GPU verfügbar – ihr nutzt ein kleines Modell über OpenRouter“ | Nichts zu tun: Das Notebook schaltet selbst um. Im Dashboard ggf. Vorab-Daten einblenden. |
| Ollama-Download zu langsam | Reiter „Start“ steht > 5 min bei „3/4 Modell laden“ | Unter „Erweitert“ „Gruppe 4 ohne GPU“ ankreuzen, Key von der Notfall-Folie, „Speichern“. |
| Rate-Limit / Ausfall eines Anbieters | ⚠️-Meldungen, viele „unlesbar“-Zellen | Weiterlaufen lassen (Retries); bei Fehlern lässt sich der Schritt erneut starten. Notfalls Probemodus (Erweitert): Läufe landen in `<session>-mock` und zählen nicht – der Mock meldet die echte Defektzeile, also nicht vor der Challenge nutzen. Vorab-Daten zeigen. |
| Scoreboard nicht erreichbar | Dashboard aktualisiert nicht; Statuszeile im Notebook „Scoreboard ⚠️“ | Läufe landen in `/content/scoreboard_backup.csv` der Gruppen; später per Instructor-Notebook („Sicherung nachsenden“) einspielen. Bis dahin Notfall-Folie. |
| WLAN-Probleme | Start hängt beim Klonen | Hotspot; sonst Notfall-Folie mit Vorab-Daten und Diskussion anhand der Thesen. |
| Gutachten falsch abgegeben | Gruppe meldet sich | Reiter 1 → „Erweitert“ → „Gutachten korrigieren“. Die Korrektur ersetzt das erste Gutachten im Dashboard. |
| Einreichung versehentlich verbraucht (Absturz während des Laufs) | Zähler steht höher als gewollt | Code-Zelle einfügen und `from judge_lab import ui; ui.SESSION.submissions_used -= 1` ausführen (der Zähler liegt nur in ihrer Colab-Sitzung). |
| Veraltete Notebook-Kopie | Spalte `notebook_version` im Sheet | Gruppe öffnet das Notebook neu über den QR-Code. |

## Nach der Session

- [ ] Alle OpenRouter-Keys widerrufen, Tab `keys` leeren.
- [ ] Sheet als CSV exportieren und archivieren.
- [ ] Kosten notieren (Instructor-Notebook „Kosten“).
