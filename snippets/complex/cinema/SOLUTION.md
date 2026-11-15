# cinema – Lösung (CL5, complexipy 30)

> **Achtung, Lösung:** Diese Datei beschreibt die eingebauten Defekte. Sie wird im Hands-on-Notebook nie angezeigt und darf nicht in einen Judge-Prompt gelangen.

## Tests ausführen

Im Terminal aus diesem Ordner heraus: `python -m pytest tests.py`. Die Tests schlagen absichtlich fehl (siehe unten). Die Projekt-Testsuite prüft automatisch, dass sie auf dem korrigierten Code (alle Korrekturen aus `meta.yaml`) grün laufen (`tests/test_ground_truth.py`).

## Eingebaute Fehler

### cinema.py – semantische Fehler

| # | Zeile | Fehler (Code) | Richtig wäre | Auswirkung |
|---|---|---|---|---|
| B1 | Z. 41–46 | `for seat in seats:`<br>`if not self.is_valid(row, seat):`<br>`raise ValueError("Diesen Platz gibt es nicht.")`<br>`if (row, seat) in self.booked:`<br>`raise ValueError("Der Platz ist schon belegt.")`<br>`self.booked.add((row, seat))` | `for seat in seats:`<br>`if not self.is_valid(row, seat):`<br>`raise ValueError("Diesen Platz gibt es nicht.")`<br>`if (row, seat) in self.booked:`<br>`raise ValueError("Der Platz ist schon belegt.")`<br>`for seat in seats:`<br>`self.booked.add((row, seat))` | Buchung ist nicht atomar: Plätze vor einem ungültigen oder belegten Platz bleiben gebucht. |
| B2 | Z. 53 | `for first in range(1, self.seats_per_row - n + 1):` | `for first in range(1, self.seats_per_row - n + 2):` | Find_block prüft den letzten möglichen Block einer Reihe nicht (Off-by-one in `range`). |
| B3 | Z. 61 | `if row > self.rows - LOGE_ROWS - 1:` | `if row > self.rows - LOGE_ROWS:` | Die letzten drei statt zwei Reihen kosten den Logenpreis. |
| B4 | Z. 40 | `raise ValueError("Mindestens ein Platz.")` | danach einfügen: `if len(set(seats)) != len(seats):`<br>`raise ValueError("Jeder Platz darf nur einmal vorkommen.")` | Fehlende Prüfung: derselbe Platz kann mehrfach in einer Buchung stehen (wird einmal gebucht, aber mehrfach gezählt). |
| B5 | Z. 83 | `return self.seats_per_row - len(self.booked)` | `return self.seats_per_row - len([seat for seat in self.booked if seat[0] == row])` | Free_seats_in_row zieht die gebuchten Plätze aller Reihen ab statt nur die der gefragten Reihe. |
| B6 | Z. 86 | `return self.booked` | `return set(self.booked)` | Booked_seats gibt das interne Set zurück statt einer Kopie; spätere Buchungen ändern die „Momentaufnahme“. |

Fehlschlagende Tests (7 von 26):

| Test | Ursache |
|---|---|
| `TestBooking::test_failed_booking_books_nothing` | Fehler B1 |
| `TestBooking::test_booking_with_invalid_last_seat_books_nothing` | Fehler B1 |
| `TestFindBlock::test_block_at_end_of_row` | Fehler B2 |
| `TestPrice::test_row_before_loge_has_normal_price` | Fehler B3 |
| `TestBooking::test_seat_twice_in_one_booking_is_rejected` | Fehler B4 |
| `TestOverview::test_free_seats_in_row_counts_only_that_row` | Fehler B5 |
| `TestOverview::test_booked_seats_is_a_snapshot` | Fehler B6 |

### cinema.py – programmatische Fehler (Code-Qualität)

Diese Fehler ändern das Verhalten nicht und lassen keinen Test fehlschlagen.

| # | Zeile | Fehler (Code) | Richtig wäre | Problem |
|---|---|---|---|---|
| Q1 | Z. 18 | `import math` | Zeile(n) entfernen | Ungenutzter Import `math`. |
| Q2 | Z. 69 | `print("Preis berechnet")` | Zeile(n) entfernen | Unerreichbarer Code nach `return`. |
| Q3 | Z. 76–77 | `if (row, seat) in self.booked:`<br>`self.booked.remove((row, seat))` | `self.booked.remove((row, seat))` | Überflüssige Bedingung: nach der Prüfung oben sind alle Plätze sicher gebucht. |
| Q4 | Z. 92 | `label = ""` | Zeile(n) entfernen | Toter Wert: `label = ""` wird sofort überschrieben. |

## Köder (korrekter Code)

Diese Stellen sehen verdächtig aus, sind aber richtig. Meldet ein Judge sie als Bug, ist das ein Fehlalarm (−1).

| Zeile | Code | Warum richtig |
|---|---|---|
| Z. 89 | `return round(len(self.booked) / (self.rows * self.seats_per_row) * 100, 1)` | Richtig: echte Division und Rundung auf eine Nachkommastelle. |
| Z. 36 | `return 1 <= row <= self.rows and 1 <= seat <= self.seats_per_row` | Grenzen richtig: Zählung ab 1, letzte Reihe und letzter Platz eingeschlossen. |
| Z. 65 | `if len(seats) >= GROUP_SIZE:` | `>=` ist richtig: Rabatt ab 6 Plätzen. |
| Z. 73 | `if (row, seat) not in self.booked:` | Stornieren ist richtig atomar: erst alle Plätze prüfen, dann freigeben. |
