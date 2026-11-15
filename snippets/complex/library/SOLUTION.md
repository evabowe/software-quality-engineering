# library – Lösung (CL3, complexipy 20)

> **Achtung, Lösung:** Diese Datei beschreibt die eingebauten Defekte. Sie wird im Hands-on-Notebook nie angezeigt und darf nicht in einen Judge-Prompt gelangen.

## Tests ausführen

Im Terminal aus diesem Ordner heraus: `python -m pytest tests.py`. Die Tests schlagen absichtlich fehl (siehe unten). Die Projekt-Testsuite prüft automatisch, dass sie auf dem korrigierten Code (alle Korrekturen aus `meta.yaml`) grün laufen (`tests/test_ground_truth.py`).

## Eingebaute Fehler

### library.py – semantische Fehler

| # | Zeile | Fehler (Code) | Richtig wäre | Auswirkung |
|---|---|---|---|---|
| B1 | Z. 60 | `if self.count_loans(member) > MAX_LOANS:` | `if self.count_loans(member) >= MAX_LOANS:` | Ein viertes Buch kann ausgeliehen werden (`>` statt `>=`). |
| B2 | Z. 64–65 | `self.loans[title] = (member, day)`<br>`` | danach einfügen: `self.reservations.pop(title, None)` | Die Reservierung endet nicht mit der Ausleihe durch die reservierende Person: Danach bleibt das Buch für alle anderen gesperrt. |
| B3 | Z. 76 | `self.fees[member] = fee` | `self.fees[member] = self.fees.get(member, 0.0) + fee` | Gebühren mehrerer Ausleihen werden überschrieben statt addiert. |
| B4 | Z. 49–50 | `raise ValueError("Das Buch ist schon reserviert.")`<br>`self.reservations[title] = member` | danach einfügen: `if self.loans[title] is None:`<br>`raise ValueError("Nur ausgeliehene Bücher können reserviert werden.")` | Fehlende Prüfung: auch ein verfügbares, nicht ausgeliehenes Buch lässt sich reservieren. |
| B5 | Z. 87 | `return start + LOAN_DAYS - 1` | `return start + LOAN_DAYS` | Due_day nennt einen Tag zu früh: die Rückgabe am Tag danach ist laut Gebührenberechnung noch kostenlos. |
| B6 | Z. 93 | `"fees": round(self.fees.get(member, 0.0)),` | `"fees": round(self.fees.get(member, 0.0), 2),` | `round` ohne Nachkommastellen rundet die Gebühren auf ganze Euro statt auf Cent. |

Fehlschlagende Tests (6 von 21):

| Test | Ursache |
|---|---|
| `TestBorrow::test_fourth_loan_is_rejected` | Fehler B1 |
| `TestReservation::test_reservation_ends_with_the_loan` | Fehler B2 |
| `TestFees::test_fees_of_several_loans_add_up` | Fehler B3 |
| `TestReservation::test_available_book_cannot_be_reserved` | Fehler B4 |
| `TestOverview::test_due_day_is_last_free_day` | Fehler B5 |
| `TestOverview::test_member_summary_with_fees_to_the_cent` | Fehler B6 |

### library.py – programmatische Fehler (Code-Qualität)

Diese Fehler ändern das Verhalten nicht und lassen keinen Test fehlschlagen.

| # | Zeile | Fehler (Code) | Richtig wäre | Problem |
|---|---|---|---|---|
| Q1 | Z. 74–75 | `if fee < 0:`<br>`fee = 0.0` | Zeile(n) entfernen | Toter Zweig `if fee < 0`: die Gebühr ist hier immer positiv. |
| Q2 | Z. 45 | `def reserve(self, title, member, day=None):` | `def reserve(self, title, member):` | Ungenutzter Parameter `day` täuscht vor, dass Reservierungen ein Datum haben. |
| Q3 | Z. 22 | `GRACE_DAYS = 2` | Zeile(n) entfernen | Ungenutzte Konstante `GRACE_DAYS` täuscht eine Kulanzfrist vor, die es nicht gibt. |

## Köder (korrekter Code)

Diese Stellen sehen verdächtig aus, sind aber richtig. Meldet ein Judge sie als Bug, ist das ein Fehlalarm (−1).

| Zeile | Code | Warum richtig |
|---|---|---|
| Z. 92 | `"reservations": list(self.reservations.values()).count(member),` | Richtig: zählt genau die Reservierungen dieses Mitglieds. |
| Z. 62 | `if self.fees.get(member, 0.0) > MAX_OPEN_FEES:` | `>` ist richtig: genau 5 EUR offene Gebühren sind noch erlaubt. |
| Z. 71 | `late_days = day - start - LOAN_DAYS` | Richtig gerechnet: Rückgabe an Tag 15 nach Ausleihe an Tag 1 ist noch pünktlich. |
