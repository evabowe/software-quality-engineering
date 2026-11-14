# Adaption der Rollen-Prompts aus dem Paper

Die Original-Prompts (`original/`, aus Sherlin-star/ai-as-a-judge) bewerten C++-Signalverarbeitungscode nach dem **VMA-Index 4.0** („Sensory Intent Mapping“). Unsere Snippets sind Python-Algorithmen mit dokumentierten Defekten. Wir behalten deshalb die **unabhängige Variable** des Papers, die Haltung des Judges (strict / objective / lenient), und tauschen das **Messinstrument** aus: ISO/IEC 25010 statt VMA-Index.

Ein Judge-Prompt besteht aus vier Blöcken in fester Reihenfolge:

1. **Haltungsblock**: `attitudes/<haltung>.md`; in Auftrag 2 der Text der Gruppe (Ausgangspunkt `challenge_baseline.md` = objective)
2. **Bewertungsskala**: `scale_iso25010.md`
3. **Aufgabe**: `task_template.md` mit nummeriertem Code, Hinweis auf die Spezifikation und optional den Tests (`tests_block.md`)
4. **Ausgabevertrag**: `output_contract.md` (JSON; wird immer angehängt und ist nicht editierbar)

Block 1 und 2 bilden die System-Message, Block 3 und 4 die User-Message.

## Was übernommen wurde

| Element | strict | objective | lenient |
|---|---|---|---|
| Rolle | Chief Embedded Software Architect | Senior System Engineer | Technical Product Manager / Rapid Prototype Developer |
| Grundhaltung | Skepsis, Nulltoleranz | Pragmatismus, Abwägung | Toleranz, Prototyp-Perspektive |
| Startpunktzahl je Dimension | 3 | 5–6 | 7 |
| Besondere Regel | vor der Bewertung mindestens drei Mängel nennen | – | „keine fatalen Bugs wie Endlosschleifen“ |

## Was geändert wurde

| Original | Adaptiert | Begründung |
|---|---|---|
| VMA-Index 4.0 mit 8 Dimensionen (Recovery, Heuristic, Mapping, Efficiency, Stability, Safety, Engineering, Transparency) | 4 Dimensionen nach ISO/IEC 25010: functional_correctness 40 %, reliability 20 %, maintainability 25 %, readability 15 % | Die VMA-Dimensionen messen, ob „sensorische“ Begriffe in Filterformeln übersetzt werden. Für Algorithmen mit Spezifikation laufen sie ins Leere. ISO 25010 passt zum Modul Software Quality Engineering. |
| Eingabe: „Original Prompt + generated C++ code“ | Eingabe: Python-Code mit Zeilennummern, Spezifikation im Docstring bzw. String am Dateiende, optional Tests | Unsere Snippets sind nicht KI-generiert; die Spezifikation steht im Code. |
| Sensorische Begriffe („sticky“, „dragging sensation“), α-Parameter, Fensterbreite N | entfernt | Domänenspezifisch für Signalverarbeitung. |
| C++-Spezifika (`std::vector::erase(begin)`, `new`, Klassenkapselung mit privaten Zustandsvariablen) | entfernt bzw. verallgemeinert zu „toter Code, unerreichbarer Code, ungenutzte Parameter“ | Kommt in Python-Snippets nicht vor; die verallgemeinerten Punkte entsprechen den Qualitätsdefekten in `bank_account`. |
| Cold-Start-Initialisierung, NaN/Inf-Prüfung (strict, objective) | verallgemeinert zu „Randfälle, ungültige Eingaben, Terminierung“ | Gleiche Idee (Robustheit), ohne Bezug zu Messsignalen. |
| strict: „Zero tolerance for performance flaws“ | „Zero tolerance for correctness flaws“ | Die Snippets enthalten keine Performance-Defekte; die Strenge soll sich auf das richten, was die Ground Truth misst. |
| objective: Bottom Line `vector::erase(begin)` | Bottom Line „falsches Ergebnis für gültige Eingaben oder fehlende Terminierung“ | Gleiche Funktion der Regel (eine harte Grenze), passend zu den Snippets. |
| Ausgabe als Markdown-Text (Defektliste, Scores, Gesamtscore) | JSON nach festem Schema | Maschinell auswertbar (Matching gegen die Ground Truth). |
| Gesamtscore vom LLM berechnet | Gesamtscore berechnet `judge_lab.scoring`; der LLM-Wert wird nur zusätzlich gespeichert | LLMs rechnen unzuverlässig. |
| Szenario-Block („Experiment Group“, Formel, Key Points) | entfernt | Diese Hinweise wären snippetspezifisch und würden die Ground Truth teilweise verraten. |

## Weitere Abweichungen vom Paper

| Paper | Hands-on | Begründung |
|---|---|---|
| 4 Judges, darunter Doubao | ein frei wählbares Modell über OpenRouter, Standard `openai/gpt-6-luna` | Die Gruppen vergleichen Prompts, nicht Modelle; ein günstiges Standardmodell hält die Kosten klein. |
| Temperatur nicht 0 | Temperatur 0 | Reproduzierbarkeit in einer kurzen Live-Session. |
| keine Ground Truth | Ground Truth: Judge-Score = 2 × gefundene Defekte − 1 × Fehlalarme | Kern unserer Erweiterung. |
