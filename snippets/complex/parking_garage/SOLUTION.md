# parking_garage – Lösung (CL2, complexipy 15)

> **Achtung, Lösung:** Diese Datei beschreibt die eingebauten Defekte. Sie wird im Hands-on-Notebook nie angezeigt und darf nicht in einen Judge-Prompt gelangen.

## Tests ausführen

Im Terminal aus diesem Ordner heraus: `python -m pytest tests.py`. Die Tests schlagen absichtlich fehl (siehe unten). Die Projekt-Testsuite prüft automatisch, dass sie auf dem korrigierten Code (alle Korrekturen aus `meta.yaml`) grün laufen (`tests/test_ground_truth.py`).

## Eingebaute Fehler

### parking_garage.py – semantische Fehler

| # | Zeile | Fehler (Code) | Richtig wäre | Auswirkung |
|---|---|---|---|---|
| B1 | Z. 33 | `if minutes < FREE_MINUTES:` | `if minutes <= FREE_MINUTES:` | Genau 30 Minuten sind nicht kostenlos (`<` statt `<=`). |
| B2 | Z. 39 | `hours = rest // 60` | `hours = -(-rest // 60)` | Nur volle statt angefangene Stunden werden berechnet (abgerundet statt aufgerundet). |
| B3 | Z. 41 | `return full_days * HOURLY_RATE * 24 + day_fee` | `return full_days * DAILY_CAP + day_fee` | Volle Tage kosten 48 EUR statt des Tageshöchstsatzes von 15 EUR. |
| B4 | Z. 71 | `due = fee` | `due = max(fee - already_paid, 0.0)` | Beim erneuten Bezahlen wird der volle Betrag statt nur der Differenz zum bereits Bezahlten fällig. |
| B5 | Z. 95 | `return len(self.parked) // self.capacity * 100` | `return len(self.parked) / self.capacity * 100` | Ganzzahldivision: die Auslastung ist 0 %, solange das Parkhaus nicht voll ist. |
| B6 | Z. 98 | `minutes = self.parked[plate] - time` | `minutes = time - self.parked[plate]` | Die Parkdauer wird mit vertauschten Werten berechnet und ist negativ. |

Fehlschlagende Tests (7 von 22):

| Test | Ursache |
|---|---|
| `TestParkingFee::test_started_hour_is_charged` | Fehler B2 |
| `TestParkingFee::test_second_started_hour_is_charged` | Fehler B2 |
| `TestParkingFee::test_full_day_costs_daily_cap` | Fehler B3 |
| `TestParkingFee::test_full_day_plus_hours` | Fehler B3 |
| `TestGarage::test_paying_again_charges_only_the_difference` | Fehler B4 (zusätzlich B2) |
| `TestReports::test_occupancy_in_percent` | Fehler B5 |
| `TestReports::test_receipt_shows_duration_and_fee_so_far` | Fehler B6 |

Fehler B1 wird von B2 verdeckt: Solange abgerundet wird, kosten 30 Minuten ohnehin 0 EUR. `test_exactly_30_minutes_is_free` schlägt erst fehl, wenn nur B2 korrigiert ist.

### parking_garage.py – programmatische Fehler (Code-Qualität)

Diese Fehler ändern das Verhalten nicht und lassen keinen Test fehlschlagen.

| # | Zeile | Fehler (Code) | Richtig wäre | Problem |
|---|---|---|---|---|
| Q1 | Z. 35–36 | `if minutes == 0:`<br>`return 0.0` | Zeile(n) entfernen | Toter Zweig `if minutes == 0`: kurze Parkdauern sind schon vorher abgehandelt. |
| Q2 | Z. 84 | `return None` | Zeile(n) entfernen | Unerreichbarer Code nach `raise`. |
| Q3 | Z. 91 | `def free_spaces(self, time=None):` | `def free_spaces(self):` | Ungenutzter Parameter `time` täuscht eine Abhängigkeit von der Uhrzeit vor. |
| Q4 | Z. 52 | `self.opened_at = 0` | Zeile(n) entfernen | Ungenutztes Attribut `opened_at`. |

## Köder (korrekter Code)

Diese Stellen sehen verdächtig aus, sind aber richtig. Meldet ein Judge sie als Bug, ist das ein Fehlalarm (−1).

| Zeile | Code | Warum richtig |
|---|---|---|
| Z. 27 | `return f"{minutes // 60} h {minutes % 60:02d} min"` | Ganzzahldivision und Rest sind hier richtig: volle Stunden und restliche Minuten. |
| Z. 57 | `if len(self.parked) >= self.capacity:` | `>=` ist richtig: sind so viele Autos drin wie Plätze, ist das Parkhaus voll. |
| Z. 85 | `if time - paid_at > EXIT_WINDOW:` | `>` ist richtig: genau 15 Minuten nach dem Bezahlen darf man noch ausfahren. |
| Z. 64 | `if plate in self.season_tickets:` | Reihenfolge richtig: Dauerparker zahlen auch bei verlorenem Ticket nichts. |
