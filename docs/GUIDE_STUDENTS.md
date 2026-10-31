# Hands-on: LLM-as-a-Judge – Kurzanleitung

**Worum geht es?** Große Sprachmodelle (LLMs) werden zunehmend als „Judges“ eingesetzt, die Code bewerten. Im Paper, das ihr gerade gesehen habt, wurde gemessen, *wie* LLMs bewerten – aber nicht, *ob sie recht haben*. Das holen wir nach: Unsere sechs Code-Beispiele enthalten **bekannte Defekte**. So sehen wir, wie viele davon ein Judge findet und wie oft er Fehlalarm schlägt.

## So geht's

1. **Notebook öffnen:** QR-Code auf der Folie scannen oder Link öffnen → Google Colab. Ein Google-Konto genügt; installieren müsst ihr nichts.
2. **⚙️ 1 · Setup:** Zelle mit ▶ starten, eure **Gruppe** wählen, den **API-Key** von der Folie eintragen, „Speichern“.
   **Gruppe 4** startet danach sofort die Zelle „🖥️ lokales Modell“ – der Download dauert ein paar Minuten.
3. **🔮 2 · Prognose:** Tippt, welcher Judge am meisten findet und ob „strict“ mehr Fehler findet als „lenient“.
4. **🧪 3 · Auftrag 1:** Ein Klick. Euer Judge bewertet alle Beispiele in drei Haltungen, mit und ohne Tests. Ihr seht pro Beispiel den Score und wie viele Defekte gefunden wurden. Besprecht die Leitfragen im Notebook.
5. **🏆 4 · Auftrag 2 – Prompt-Challenge:** Schreibt einen eigenen Judge-Prompt, der möglichst viele echte Defekte findet.
   - **Punkte:** +2 pro gefundenem Defekt, −1 pro Fehlalarm.
   - **Probeläufe** auf einem Beispiel: so oft ihr wollt.
   - **Einreichungen:** maximal **3**; sie laufen immer über alle sechs Beispiele.
   - **Fair bleiben:** keine Hinweise auf bestimmte Zeilen oder Funktionen – der Prompt muss allgemein funktionieren.
6. **Auswertung** am Beamer: Was hat euch überrascht?

## Wenn etwas hakt

- Eine gelbe ⚠️-Meldung erklärt, was fehlt (z. B. Setup nicht ausgeführt, Key fehlt). Sonst: Hand heben, Eva oder Jessica kommen vorbei.
- Ihr müsst den Code in den Zellen weder lesen noch ändern.

## Datenschutz

An die KI-Anbieter (über OpenRouter) gehen nur der Beispielcode und euer Prompt. Auf dem Scoreboard gespeichert werden nur eure Gruppennummer, die Ergebnisse und eingereichte Prompts – keine Namen oder andere personenbezogenen Daten.
