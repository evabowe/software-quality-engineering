# Offene Fragen aus dem Umbau (11.11.2026)

Beim Umsetzen von [2026-11-11-interaktive-session.md](2026-11-11-interaktive-session.md) entschieden, aber von Eva bzw. dem Team zu bestätigen. Jede Entscheidung ist mit einer Konstante oder wenigen Zeilen änderbar.

## Didaktik und Ablauf

1. **Streuung / H3 (AP4, optional P3) ist nicht umgesetzt.** Es gibt keinen Button „3× wiederholen“. → „Streuung“ und H3 von den Folien streichen – oder Bescheid geben, dann wird es nachgerüstet (`phase="a1_repeat"`, `temperature=0.7`).
2. **Welche Notebook-Reiter öffnet Dashboard-Ansicht ②?** Laut Zeitplan laufen Schritt 2 *und* Schritt 3 in Minute 20–32. Deshalb öffnet ② die Reiter 2 **und 3** (Phase 3), ③ ändert nichts mehr. Die Zahlen 0–5 im Admin-Kasten setzen die Phase bei Bedarf genau. (`VIEW_PHASE` in `scoreboard/dashboard.html`)
3. **H2 „bester Judge“ wird auf `bank_account` aufgelöst** – nur diesen Code haben auch die Menschen bewertet, sonst wäre „wir Menschen“ nicht vergleichbar. Daneben steht der beste LLM-Judge über alle Beispiele. Passt das zur Moderation?
4. **H1 „strict vs. lenient“** wird über den Ø Recall aller Läufe aufgelöst; ein Unterschied unter 0,1 gilt als „etwa gleich“ (`RECALL_TIE` in `scoreboard/Code.gs`). Bei nur 4 Gruppen ist das ein grobes Maß – soll die Schwelle anders sein?
5. **Rollen in ② erst nach „Rollen aufdecken“.** Die Matrix Mensch vs. LLM ordnet die Gutachten den Rollen-Spalten zu und würde die Rollen sonst verraten. Wer ① moderiert, sollte also am Ende von ① aufdecken.
6. **Leeres Gutachten:** „keine“ (oder „-“) ist als „keine Fehler gefunden“ erlaubt; ein leeres Feld nicht. Eine Begründung ist Pflicht.
7. **Methodenpool:** Wird „Gutachten erstellen“ + „AI Challenge“ freigegeben? Die Vernissage ist aus CONCEPT.md und RUNBOOK.md entfernt (steht nicht im Pool); die Prompt-Galerie läuft als Teil der AI Challenge.

## Inhalt

8. **Paper-Werte (Chou 2026, Tabelle 6)** sind wie im Plan übernommen und als strict / objective / lenient gelesen (strict ist bei allen vier Modellen am niedrigsten). Bitte einmal gegen das Paper prüfen (`PAPER` in `scoreboard/Code.gs`).
9. **Rollenkarten** (`prompts/role_cards_de.md`): Die strict-Karte enthält „Nennt mindestens drei konkrete Mängel“ aus dem Audit-Protokoll des Haltungsblocks. Das ist abgeleitet, nicht hinzugefügt – aber es lenkt Gruppe 1 stärker als die anderen. Behalten?

## Sicherheit

10. **Gruppencodes und öffentliches Token:** `?action=join` verlangt das Scoreboard-Token, das im öffentlichen Repo steht. Es schützt also nur vor Zufallstreffern; wer das Token kennt, kann Codes raten (4 Zeichen aus 32 → ca. 1 Mio. Möglichkeiten, Apps Script ist langsam). Gegenmittel: Keys mit kleinem Kreditlimit, pro Session neue Codes, nach der Session widerrufen (steht so in GUIDE_INSTRUCTOR.md). Reicht das?
11. **Rollen und Ground Truth im JSON:** `?format=json` ist öffentlich und enthält (wie bisher die Ground Truth) auch die Rollen der Gutachten. Wer die URL kennt und das JSON liest, kann vorab spicken. Bisher als akzeptabel angesehen – weiterhin?
