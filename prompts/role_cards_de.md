<!--
Rollenkarten für Schritt 1 („Gutachten erstellen“). Eine Karte pro Haltung; welche Gruppe welche
Karte bekommt, steht in judge_lab/config.py (HUMAN_ROLES). Die Texte sind deutsche Kurzfassungen
der Haltungsblöcke in prompts/attitudes/*.md (Rolle, Grundhaltung, Startpunktzahl) – nichts hinzufügen.
Je Karte höchstens 5 Zeilen; **fett** wird in der Oberfläche fett dargestellt.
-->

## strict
**Rolle:** Chief Embedded Software Architect mit 15 Jahren Erfahrung in Luftfahrt oder Medizintechnik.
**Haltung:** Null Toleranz bei Korrektheitsfehlern. Ihr geht davon aus, dass jeder Code versteckte Probleme hat; Randfälle, ungültige Eingaben und Terminierung zählen, toter Code ist ein Mangel.
**Vorgehen:** Nennt mindestens drei konkrete Mängel, bevor ihr einen Score vergebt.
**Starte bei 3 Punkten.** Nur eine perfekte Umsetzung bekommt mehr.

## objective
**Rolle:** Senior System Engineer.
**Haltung:** Taugt der Code für den Produktivbetrieb? Pragmatisch: robust, lesbar, logisch konsistent. Nicht optimierter Code ist in Ordnung – falsche Ergebnisse bei gültigen Eingaben oder ein Programm, das nicht endet, nicht.
**Starte bei 5–6 Punkten** (Niveau einer qualifizierten Fachkraft): Pluspunkte für klare Stärken, Abzüge für logische Risiken.

## lenient
**Rolle:** Technical Product Manager bzw. Prototyp-Entwickler.
**Haltung:** Trifft der Code die Absicht seiner Spezifikation? Wenn die Kernidee stimmt, ist die Aufgabe weitgehend gelöst. Randfälle und ungültige Eingaben müssen nicht behandelt werden, etwas Redundanz ist in Ordnung.
**Starte bei 7 Punkten.** Ohne fatale Fehler wie Endlosschleifen ist der Code als erster Entwurf sehr gut.

## none
Bewertet nach eurem eigenen Urteil.
