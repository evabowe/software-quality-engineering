# Hands-on „LLM-as-a-Judge für Softwarequalität“ – Konzept

**Session:** 19.11.2026, 75 min interaktiv (seit 11.11.2026, vorher 45 min Hands-on) · **Verantwortlich Infrastruktur/roter Faden:** Eva

Abschnitte 1, 3 und 4 entsprechen dem Konzept vom 31.10.2026; Abschnitt 2 und die Ansichten in Abschnitt 4 folgen dem Umbau auf 75 Minuten (`docs/plans/2026-11-11-interaktive-session.md`). Abschnitt 5 beschreibt den Stand der Umsetzung und alle Abweichungen. Das vollständige Konzept inklusive Implementierungsteil liegt unter `docs/superpowers/specs/2026-10-31-judge-lab-design.md`.

---

## 1. Leitidee und roter Faden

Das Paper (Chou 2026, *AI-as-a-Judge for software quality assessment*, SQJ 34:48) untersucht 4 LLM-Judges × 3 Haltungen (strict / objective / lenient) und beantwortet drei Fragen:

- **RQ1** Wie konsistent sind verschiedene Judges? → nur moderat (ICC 0.46–0.57)
- **RQ2** Verändern Rollen-Prompts das Urteil? → stark (Cohen's d > 0.9)
- **RQ3** Beeinflusst Code-Komplexität die Scores? → ja, aber kleine bis mittlere Effekte

Das Paper verzichtet **bewusst auf eine Ground Truth** („machine psychometrics“): Es misst nur, *wie* Judges bewerten, nicht, *ob sie recht haben*.

**Unser Hands-on ist eine Mini-Replikation mit Ground Truth.** Wir verwenden Code mit **bekannten, dokumentierten Defekten** und können deshalb messen, was das Paper nicht misst: Recall und False Positives der Judges.

Roter Faden durch die Gesamtveranstaltung:

```
Theorie (Jessica) → Paper RQ1–3 (Alea) → Kritik: "keine Ground Truth" (Alea)
   → Hands-on: "Was sehen wir, wenn wir die Ground Truth kennen?" (Eva)
   → Auswertung: zurück zu RQ1–3 + eigene Zusatzbefunde
   → Abschluss: Wiederholung der Umfrage von Folie 5 („Würdest du einem LLM das Code-Review überlassen?“)
```

Eigene Zusatzfaktoren über das Paper hinaus:

1. **Ground Truth** → Recall / False Positives statt nur Scores
2. **Mit vs. ohne Tests als Kontext** → hilft Testcode dem Judge?
3. **Bekannter Benchmark (QuixBugs) vs. eigenes Beispiel (bank_account)** → Hinweis auf Data Contamination (QuixBugs ist seit 2017 öffentlich und vermutlich in den Trainingsdaten)
4. **Prompt-Challenge** → Prompt-Engineering für Fehlerfindung statt für Strenge

---

## 2. Ablauf der 75 Minuten (mit Methoden aus dem Methodenpool CAU Kiel)

Vorgaben der Dozentin: höchstens 75 min, so interaktiv und anwendungsorientiert wie möglich, mindestens zwei Methoden aus dem Methodenpool, die keine andere Gruppe nutzt. Unsere Wahl (vorbehaltlich Freigabe): **Gutachten erstellen** und **AI Challenge**, optional **Heißer Stuhl**.

Die Session ist **aufbauend**: Erst urteilen die Studierenden selbst, dann urteilt das LLM über denselben Code, dann über alle Beispiele, zum Schluss schreiben die Gruppen eigene Judge-Prompts. Im Notebook führt eine Oberfläche mit Reitern durch die Schritte; die Lehrenden schalten die Reiter vom Dashboard aus frei.

| Min. | Phase | Methode | Inhalt | Wer |
|---|---|---|---|---|
| 0–5 | Ankommen, Setup, Vorher-Umfrage | Clicker (Menti) | QR-Code → Colab (Gruppe 4: zweiter QR-Code, GPU-Notebook). ▶ Start, Gruppencode von der Folie eintippen. Dashboard: „4/4 Gruppen verbunden“. | Eva |
| 5–15 | ① Ihr seid der Judge | **Gutachten erstellen** | Jede Gruppe bewertet `bank_account` in einer **verdeckten Rolle** (Gruppe 1 strict, 2 objective, 3 lenient, 4 ohne Rolle = Kontrollgruppe): Fehlerzeilen, Score 1–10, ein Satz Begründung. Rückmeldung nur „x von 6 gefunden“. Dashboard: Scores je Gruppe, dann „Rollen aufdecken“. | Jessica |
| 15–20 | Mini-Input LLM-as-a-Judge | – | Folien | Jessica |
| 20–32 | ② Gleicher Code, LLM als Judge | – | Prognose (H1 strict vs. lenient, H2 bester Judge inkl. „wir Menschen“) → das LLM bewertet `bank_account` in drei Haltungen → Vergleichstabelle Mensch vs. LLM mit drei Leitfragen → Schritt 3: die übrigen fünf Beispiele laufen im Hintergrund. Dashboard: Mensch vs. LLM, Heatmaps. | Eva |
| 32–44 | ③ Paper vs. wir, Kritik | Heißer Stuhl (optional) | Ø Scores aus Chou (2026), Tabelle 6, neben unseren; dann „Und der Recall?“ – was das Paper ohne Ground Truth nicht sehen kann. | Alea |
| 44–64 | ④ Prompt-Challenge | **AI Challenge** | Eigener Judge-Prompt, Probeläufe unbegrenzt, **max. 3 Einreichungen** über alle 6 Beispiele; +2 je Treffer, −1 je Fehlalarm. Live-Leaderboard. Die **Prompt-Galerie** (beste Einreichung je Gruppe) ist Teil der Challenge: Gewinnergruppe erklärt ihren Prompt, Plenum stimmt über die beste Erklärung ab. | Eva |
| 64–70 | Auflösung, Prognose-Check, Nachher-Umfrage | Clicker | Ground Truth, Prognose vs. Ergebnis, Wiederholung der Umfrage. | Alea |
| 70–75 | Blitzlicht + Ausblick | **Blitzlicht** | „Würde ich einen LLM-Judge in die CI einbauen – unter welcher Bedingung?“ | alle |

**Zeitpuffer:** Wird es knapp, wird die Challenge auf 2 Einreichungen gekürzt (mündlich ansagen). Die Auflösung wird nicht gekürzt.

Optional ganz am Ende (mit dem Team abstimmen): **Fünf-Finger-Methode** als Feedback zur Lehreinheit.

---

## 3. Code-Beispiele (Vorauswahl, mit Jessica abzustimmen)

### 3.1 Quelle und Lizenz

- **QuixBugs** – https://github.com/jkoppel/QuixBugs, MIT-Lizenz, © 2017–2019 James Koppel.
  Referenz: Lin, Koppel, Chen, Solar-Lezama (2017): *QuixBugs: A Multi-Lingual Program Repair Benchmark Set Based on the Quixey Challenge*, SPLASH Companion.
  40 Programme, jeweils **genau ein einzeiliger Defekt**, korrigierte Version und Testfälle mitgeliefert.
- **bank_account** – eigenes Lehrbeispiel (Jessica), 3 semantische + 3 Code-Qualitäts-Defekte, dokumentiert in `src/code_with_defects/README.md`.

Die QuixBugs-Dateien werden **unverändert** übernommen (Zeilennummern bleiben gleich). Es werden keine Snippets von einem LLM generiert.

### 3.2 Auswahl: 5 Komplexitätsstufen + eigenes Beispiel

Kriterien: Streuung über die Komplexität (analog zu L1–L5 im Paper), unterschiedliche Defektklassen, kurze Programme (lesbar am Beamer), Docstring-Spezifikation vorhanden.

Die Komplexitätswerte sind eine eigene AST-Näherung; die finalen Werte berechnet `tools/compute_complexity.py` mit complexipy (siehe 6.2).

| ID | Programm | Stufe | Kogn. Komplexität (Näherung) | Defekt (Zeile im Originalfile) | Korrektur | Defekt-Typ |
|---|---|---|---|---|---|---|
| `qb_bitcount` | bitcount | L1 | ~1 | **Z. 5** `n ^= n - 1` | `n &= n - 1` | falscher Operator (führt zu Endlosschleife) |
| `qb_quicksort` | quicksort | L2 | ~3 | **Z. 7** `if x > pivot` | `if x >= pivot` (alternativ Z. 6 `<=`) | falscher Vergleichsoperator: Duplikate gehen verloren |
| `qb_levenshtein` | levenshtein | L3 | ~5 | **Z. 6** `return 1 + levenshtein(...)` | `return levenshtein(...)` | überzählige Arithmetik |
| `qb_shunting_yard` | shunting_yard | L4 | ~8 | **fehlende Zeile nach Z. 17** | `opstack.append(token)` im `else`-Zweig | fehlende Zeile (Defekt durch Abwesenheit) |
| `qb_next_permutation` | next_permutation | L5 | ~10 | **Z. 6** `if perm[j] < perm[i]` | `if perm[i] < perm[j]` | vertauschte Operanden im Vergleich |
| `bank_account` | eigenes Beispiel | – | 9 (complexipy) | 6 Defekte, s. 3.3 | s. README | gemischt |

Die Defektklasse laut QuixBugs-Paper (Tabelle 1) wird beim Übernehmen in `meta.yaml` nachgetragen.

**Begründung der Auswahl:**
- `bitcount` ist kurz, aber trickreich (Bit-Trick); der Defekt verursacht eine Endlosschleife → Tests brauchen einen Timeout.
- `quicksort` kennt jeder; der Fehler zeigt sich nur bei Duplikaten → gut für die Frage „hilft der Testkontext?“.
- `levenshtein` ist rekursiv; der Fehler ist eine Kleinigkeit in einer sonst korrekten Formel.
- `shunting_yard` ist didaktisch am wertvollsten: Der Defekt ist eine **fehlende Zeile**. Kann ein Judge etwas finden, das nicht da ist?
- `next_permutation` hat verschachtelte Schleifen und Indexlogik → höchste Komplexität.
- `bank_account` ist **nicht öffentlich** → Kontrolle für Data Contamination; enthält zusätzlich Code-Qualitäts-Defekte, die keine Tests brechen.

Ersatzkandidaten, falls Jessica tauschen möchte: `gcd` (L1, sehr bekannt), `rpn_eval` (L2), `kheapsort` (L2), `lis` (L4), `shortest_path_length` (L5+, 48 Zeilen – evtl. zu lang).

### 3.3 Ground Truth bank_account (aus README, geprüft gegen den Code)

| # | Zeilen | Art | Kurzbeschreibung |
|---|---|---|---|
| B1 | 26 | bug | `balance -= amount` in `deposit` |
| B2 | 31 | bug | `<=` statt `<` beim Dispo-Limit |
| B3 | 39–40 | bug | Reihenfolge Gutschrift/Abbuchung in `transfer` |
| Q1 | 24–25 | quality | toter `elif amount < 0`-Zweig |
| Q2 | 33 | quality | unerreichbarer Code nach `raise` |
| Q3 | 42 | quality | ungenutzter Parameter `days` |

Hinweis: Z. 38 enthält den Tippfehler „Überisung“. Er ist **nicht** Teil der Ground Truth. Ein Judge, der ihn meldet, bekommt dafür weder Punkte noch Abzug (Kategorie `style`, s. Matching-Regeln 6.5). Mit Jessica klären, ob er bleiben soll.

---

## 4. Messgrößen und Auswertung (Mapping auf das Paper)

| Dashboard-Ansicht | Paper-Bezug | Inhalt |
|---|---|---|
| **① Mensch: gleicher Code, andere Rolle** | Gutachten erstellen | Score je Gruppe, Rollen erst verdeckt, dann aufgedeckt |
| **② Mensch vs. LLM** | RQ2 + Ground Truth | `bank_account`: Score und Recall der Menschen je Rolle und der LLMs je Modell × Haltung |
| **③ Paper vs. wir** | RQ2 | Ø Scores aus Chou (2026), Tabelle 6, neben unseren; darunter unser Recall |
| **Heatmap Modell × Haltung: Ø Score** | RQ2 | Verschiebt die Haltung die Note? |
| **Heatmap Modell × Haltung: Recall** | RQ2 + Ground Truth | Verschiebt die Haltung auch die Fehlerfindung? (Kernfrage) |
| **Übereinstimmung der Judges** | RQ1 | Pro Defekt: welche Modelle haben ihn gefunden (Matrix Defekt × Modell); dazu Spearman-ρ der Scores zwischen Modellen |
| **Recall über Komplexitätsstufe** | RQ3 | Liniendiagramm L1–L5 je Modell |
| **Mit vs. ohne Tests** | Zusatz | Δ Recall und Δ False Positives |
| **QuixBugs vs. bank_account** | Zusatz (Validität) | Recall auf öffentlichen vs. unbekannten Code |
| **Prognose vs. Ergebnis** | Didaktik | Was hat die Gruppe erwartet? |
| **Leaderboard Prompt-Challenge** | Prompt Engineering | Punkte eigenes Modell + Punkte Referenzmodell |
| **Prompt-Galerie** | AI Challenge | Beste Einreichung je Gruppe groß; alle Einreichungen unter „Mehr“ |

**Erwartbare Diskussionsthesen** (für Moderation vorbereiten, nicht vorab verraten):
- „strict“ senkt den Score deutlich, erhöht den Recall aber kaum → *Strenge ≠ Gründlichkeit*.
- „strict“ erzeugt mehr False Positives → Strenge kostet Präzision.
- Testkontext erhöht den Recall bei `quicksort`/`bank_account`, weil Testnamen die Absicht verraten.
- `shunting_yard` (fehlende Zeile) wird seltener gefunden.
- Kleines lokales Modell: deutlich weniger Recall, mehr Formatfehler → Trade-off Datenschutz vs. Qualität.

---

## 5. Stand der Umsetzung und Abweichungen

### 5.1 Gemessene Komplexität (complexipy)

Die Näherungswerte aus 3.2 sind durch Messwerte ersetzt (`tools/compute_complexity.py`, Summe über alle Funktionen):

| Snippet | Stufe | Kognitive Komplexität | LOC (nicht-leer) |
|---|---|---|---|
| qb_bitcount | L1 | 1 | 19 |
| qb_quicksort | L2 | 6 | 14 |
| qb_levenshtein | L3 | 6 | 24 |
| qb_shunting_yard | L4 | 9 | 36 |
| qb_next_permutation | L5 | 10 | 22 |
| bank_account | – | 9 | 82 |

`quicksort` und `levenshtein` liegen gleichauf; die Stufen L1–L5 bleiben trotzdem in der geplanten Reihenfolge (manuell gesetzt). Für die Diskussion zu RQ3 lohnt der Hinweis, dass die Stufen nur grob monoton sind.

### 5.2 Ground Truth

- Alle Zeilenangaben aus 3.2 und 3.3 sind gegen QuixBugs-Commit `4257f44` bzw. `bank_account.py` geprüft.
- Die Korrekturen stehen wörtlich in `meta.yaml`. Ein Test wendet sie an und prüft, dass danach alle Tests grün sind und vorher mindestens einer fehlschlägt. Damit sind Zeilennummern und Korrekturen maschinell abgesichert.
- **Toleranzbereiche (`accept_lines`) für bank_account** sind ein Vorschlag und mit Jessica abzustimmen: B1 25–26, B2 31–32, B3 38–40, Q1 22–25, Q2 32–33, Q3 42.
- `quixbugs_class` ist aus dem Diff zur korrigierten Version abgeleitet; Tabelle 1 des QuixBugs-Papers nennt nur Klassen und Anzahlen, keine Zuordnung pro Programm.
- Den vierten levenshtein-Testfall („amanaplanacanalpanama“) überspringt QuixBugs selbst, weil die naive Rekursion minutenlang läuft; wir übernehmen deshalb die ersten 6 nicht übersprungenen Fälle.

### 5.3 Abweichungen vom Implementierungsteil des Konzepts

| # | Konzept | Umsetzung | Grund |
|---|---|---|---|
| A1 | `snippets/<id>/code.py` | Originalname, z. B. `snippets/qb_quicksort/quicksort.py`; Feld `code_file` in `meta.yaml` | `code.py` verdeckt das Standardmodul `code`. |
| A2 | Spezifikation im Docstring | bank_account: Docstring; QuixBugs: String am Dateiende (`spec: trailing_string`) | So liegen die QuixBugs-Dateien vor; der Task-Prompt nennt die richtige Stelle. |
| A3 | bank_account-Tests unverändert | nur die Import-Zeile angepasst | Der alte Paketpfad existiert nicht mehr. |
| A4 | – | pytest sammelt nur `tests/` | Die Snippet-Tests schlagen absichtlich fehl. |
| A5 | `fix` als Freitext | wörtlicher Ersatzcode + `fix_op`, zusätzlich `source.sha256` | maschinelle Prüfung der Ground Truth (5.2). |
| A6 | eigener Retry-Backoff | Retries des openai-SDK (`max_retries=3`) | gleiches Verhalten, weniger Code. |
| A7 | Ollama `format="json"` | `response_format` für beide Provider | Ollamas OpenAI-kompatibler Endpunkt versteht es. |
| A8 | Datensatzfelder 8.8 | ergänzt um `submission_no`, `prediction_*`, `error` | Einreichungen und Prognosen brauchen eigene Spalten. |
| A9 | Defekt-Matrix aus den Läufen | Ground Truth zusätzlich im Sheet-Tab `defects` (Upload aus dem Instructor-Notebook) | Sonst fehlen Defekte, die kein Modell gefunden hat. |
| A10 | Modell-IDs als Platzhalter | Stand 31.10.2026: `google/gemini-3.8-flash`, `deepseek/deepseek-v4.1-flash`, `moonshotai/kimi-k2.6`, Referenz `qwen/qwen3-coder-next`, lokal `qwen2.5-coder:3b`, Fallback ohne GPU `qwen/qwen3-coder-flash` | Kimi K2.6 statt K3: K3 kostet 15 $/M Ausgabe-Tokens und denkt als Reasoning-Modell evtl. über das Token-Limit hinaus. Eine Woche vorher prüfen. |
| A11 | – | Baseline-Prompt läuft als Gruppe „Baseline“ mit dem Referenzmodell aufs Leaderboard | Vergleichsmarke für die Prompt-Challenge. |

Die Adaption der Rollen-Prompts ist in `prompts/ADAPTATION.md` dokumentiert (Material für Aleas Kritik-Teil). Wichtig für die Auswertung: Die strict-Haltung muss laut Paper **vor** der Bewertung mindestens drei Mängel nennen; das treibt die Fehlalarme vermutlich nach oben und ist gewollt.

### 5.4 Bekannte Lücke in den Wertungsregeln

Nach Regel 3 und 5 (Konzept 8.6) zählt ein Treffer unabhängig von der Kategorie, während nicht zugeordnete `style`-Befunde neutral bleiben. Ein Challenge-Prompt wie „melde jede Zeile als style-Befund“ trifft damit alle Defekte ohne Abzug. Der Lint warnt davor nicht. Gegenmittel, falls nötig: in Auftrag 2 auch neutrale Befunde mit z. B. −0,5 werten (`POINTS` in `judge_lab/config.py` und `scoreboard/Code.gs`) oder die Regel bei der Prompt-Galerie offenlegen.
