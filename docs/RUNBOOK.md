# Runbook für den 19.11.2026 (45 min Hands-on)

Vorbereitung: [GUIDE_INSTRUCTOR.md](GUIDE_INSTRUCTOR.md). Rollen (Vorschlag, im Team bestätigen): **Eva** Ablauf und Technik, **Alea** Paper-Bezug, **Jessica** Code und Defekte.

## Am Vortag

- [ ] `DEFAULT_SESSION_ID = "2026-11-19-live"` in `judge_lab/config.py`, gleicher Wert im Sheet-Tab `config`; gepusht.
- [ ] Modell-IDs fixiert, Generalprobe 2 bestanden, Vorab-Läufe (`precomputed`) im Sheet.
- [ ] Ground Truth hochgeladen (Instructor-Notebook).
- [ ] 4 Gruppen-Keys + Instructor-Key angelegt, Limits gesetzt; Folie mit Keys und QR-Code zum Colab-Notebook.
- [ ] Screenshot des Dashboards mit Vorab-Daten als Notfall-Folie.

## 15 Minuten vorher

- [ ] Dashboard am Beamer öffnen (`…/exec`), Session prüfen, Schalter „Vorab-Daten“ **aus**.
- [ ] Instructor-Notebook in Colab geöffnet und Setup ausgeführt.
- [ ] Eigener Laptop: ein Gruppen-Notebook im Probemodus (Mock) einmal durchklicken.

## Minutenplan

| Min. | Phase | Was passiert | Wer |
|---|---|---|---|
| 0–5 | Setup | QR-Code zeigen. 4 Zweiergruppen, jede Gruppe = ein Judge. **Gruppe 4 startet sofort die Ollama-Zelle.** Alle: Setup-Zelle, Gruppe wählen, Key eintragen. | Eva |
| 5–7 | Prognose | Think/Pair: zwei Dropdowns, „Absenden“. Dashboard zeigt die Prognosen. | Gruppen |
| 7–17 | Auftrag 1 | „Auftrag 1 starten“. Während es läuft: Leitfragen im Paar. Dashboard füllt sich live. | Gruppen, Eva betreut |
| 17–32 | Auftrag 2 | Prompt-Challenge: Probeläufe, max. 3 Einreichungen. Leaderboard am Beamer. | Gruppen, Eva + Jessica betreuen |
| 32–40 | Auswertung | Vernissage am Dashboard: RQ2 (Score- und Recall-Heatmap), RQ1 (Defekt-Matrix), RQ3 (Kurve), Tests, QuixBugs vs. bank_account, Prognosen vs. Ergebnis, Prompt-Galerie. Gewinnergruppe erklärt ihren Prompt; Plenum stimmt über die beste Erklärung ab. Zum Schluss „Ground Truth anzeigen“. | Eva moderiert, Alea ordnet ins Paper ein |
| 40–45 | Abschluss | Blitzlicht: „Würde ich einen LLM-Judge in die CI einbauen – unter welcher Bedingung?“ + Wiederholung der Umfrage von Folie 5. | alle |

**Zeitpuffer:** Dauert Auftrag 1 länger, wird Auftrag 2 auf 2 Einreichungen gekürzt (mündlich ansagen; das Notebook lässt technisch 3 zu). Die Auswertung wird nicht gekürzt.

### Moderationsthesen (nicht vorab verraten)

- „strict“ senkt den Score deutlich, erhöht den Recall aber kaum → *Strenge ≠ Gründlichkeit*.
- „strict“ erzeugt mehr Fehlalarme (der Paper-Prompt verlangt mindestens drei Mängel) → Strenge kostet Präzision.
- Testkontext hilft bei `quicksort`/`bank_account`, weil Testnamen die Absicht verraten.
- `shunting_yard` (fehlende Zeile) wird seltener gefunden.
- Kleines lokales Modell: weniger Recall, mehr unlesbare Antworten → Datenschutz vs. Qualität.
- QuixBugs ist öffentlich, bank_account nicht: Ist ein höherer Recall bei QuixBugs Können oder Erinnern?

## Fallbacks

| Problem | Erkennbar an | Sofortmaßnahme |
|---|---|---|
| Keine T4-GPU für Gruppe 4 | Ollama-Zelle meldet „Keine GPU gefunden“ | Setup erneut: „Gruppe 4 ohne GPU“ ankreuzen → kleines Modell über OpenRouter. Im Dashboard ggf. Vorab-Daten einblenden. |
| Ollama-Download zu langsam | Zelle läuft > 5 min | Gruppe 4 arbeitet mit dem Fallback (siehe oben) weiter. |
| Rate-Limit / Ausfall eines Anbieters | ⚠️-Meldungen, viele „unlesbar“-Zellen | Weiterlaufen lassen (Retries). Notfalls Probemodus (Mock) ankreuzen, damit die Gruppe die Oberfläche kennenlernt; Ergebnisse aus Vorab-Daten zeigen. |
| Scoreboard nicht erreichbar | Dashboard aktualisiert nicht | Läufe landen in `/content/scoreboard_backup.csv` der Gruppen. Später per Instructor-Notebook („Sicherung nachsenden“) einspielen. Bis dahin Notfall-Folie. |
| WLAN-Probleme | Setup hängt beim Klonen | Hotspot; sonst Notfall-Folie mit Vorab-Daten und die Diskussion anhand der Thesen führen. |
| Gruppe kommt nicht weiter | — | Nur Buttons und Formulare nötig; Student-Guide; Eva und Jessica gehen herum. |
| Einreichung versehentlich verbraucht (Absturz während des Laufs) | Zähler steht höher als gewollt | Die Gruppe fügt in ihrem Notebook eine Code-Zelle ein und führt `ui.SESSION.submissions_used -= 1` aus (der Zähler liegt nur in ihrer Colab-Sitzung). |
| Veraltete Notebook-Kopie | Spalte `notebook_version` im Sheet | Gruppe öffnet das Notebook neu über den Link. |

## Nach der Session

- [ ] Alle OpenRouter-Keys widerrufen.
- [ ] Sheet als CSV exportieren und archivieren.
- [ ] Kosten notieren (Instructor-Notebook „Kosten“).
- [ ] Optional: Fünf-Finger-Feedback am Ende der 90 min.
