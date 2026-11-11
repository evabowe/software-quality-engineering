# Hands-on: LLM-as-a-Judge – Kurzanleitung

**Worum geht es?** Große Sprachmodelle (LLMs) werden zunehmend als „Judges“ eingesetzt, die Code bewerten. Heute bewertet ihr zuerst selbst Code und lasst dann ein LLM denselben Code begutachten. Unsere Beispiele enthalten **bekannte Defekte** – so sehen wir, wer wie viele davon findet.

**Ihr braucht:** einen Laptop pro Zweiergruppe und ein Google-Konto. Installieren müsst ihr nichts.

## So legt ihr los

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

## Wenn etwas hakt

Gelbe ⚠️-Meldungen sagen, was fehlt. Sonst Hand heben. Den Code in der Zelle müsst ihr weder lesen noch ändern.

## Datenschutz

An die KI-Anbieter gehen nur der Beispielcode und euer Prompt. Gespeichert werden Gruppennummer, Ergebnisse und eingereichte Prompts, keine Namen.
