# warehouse – Lösung (CL4, complexipy 25)

> **Achtung, Lösung:** Diese Datei beschreibt die eingebauten Defekte. Sie wird im Hands-on-Notebook nie angezeigt und darf nicht in einen Judge-Prompt gelangen.

## Tests ausführen

Im Terminal aus diesem Ordner heraus: `python -m pytest tests.py`. Die Tests schlagen absichtlich fehl (siehe unten). Die Projekt-Testsuite prüft automatisch, dass sie auf dem korrigierten Code (alle Korrekturen aus `meta.yaml`) grün laufen (`tests/test_ground_truth.py`).

## Eingebaute Fehler

### warehouse.py – semantische Fehler

| # | Zeile | Fehler (Code) | Richtig wäre | Auswirkung |
|---|---|---|---|---|
| B1 | Z. 47 | `batches.sort(key=lambda batch: batch[1], reverse=True)` | `batches.sort(key=lambda batch: batch[1])` | Ausgeliefert wird zuerst die Charge, die am spätesten abläuft, statt die am frühesten. |
| B2 | Z. 50 | `if batch[1] <= today:` | `if batch[1] < today:` | Eine Charge, die heute abläuft, wird nicht mehr ausgeliefert (`<=` statt `<`). |
| B3 | Z. 44 | `available = sum(batch[0] for batch in batches)` | `available = self.stock(product, today)` | Abgelaufene Chargen zählen zum verfügbaren Bestand; dann wird teilweise ausgeliefert statt gar nicht. |
| B5 | Z. 19–21 | `def __init__(self, min_stock={}):`<br>`self.batches = {}        # Produkt -> Liste von [Menge, Ablauftag]`<br>`self.min_stock = min_stock      # Produkt -> Mindestbestand` | `def __init__(self, min_stock=None):`<br>`self.batches = {}        # Produkt -> Liste von [Menge, Ablauftag]`<br>`self.min_stock = dict(min_stock or {})      # Produkt -> Mindestbestand` | Veränderlicher Standardwert `{}`: alle Lager ohne eigene Angabe teilen sich dasselbe Dict mit Mindestbeständen. |
| B6 | Z. 81 | `return max(batch[1] for batch in self.batches[product]) - today` | `return min(batch[1] for batch in self.batches[product]) - today` | Days_until_expiry nimmt die Charge, die am spätesten abläuft, statt der nächsten (`max` statt `min`). |

Fehlschlagende Tests (7 von 20):

| Test | Ursache |
|---|---|
| `TestShip::test_ship_takes_earliest_expiry_first` | Fehler B1 |
| `TestShip::test_ship_uses_batch_expiring_today` | Fehler B2 |
| `TestShip::test_expired_stock_does_not_count_and_nothing_is_shipped` | Fehler B3 |
| `TestSeveralWarehouses::test_minimums_are_per_warehouse` | Fehler B5 |
| `TestExpiredAndReorder::test_products_without_minimum_are_never_reordered` | Folgefehler von B5 (das Lager sieht Mindestbestände aus früheren Tests) |
| `TestExpiredAndReorder::test_stock_exactly_at_minimum_is_not_reordered` | Folgefehler von B5 (das Lager sieht Mindestbestände aus früheren Tests) |
| `TestOverview::test_days_until_next_expiry` | Fehler B6 |

### warehouse.py – programmatische Fehler (Code-Qualität)

Diese Fehler ändern das Verhalten nicht und lassen keinen Test fehlschlagen.

| # | Zeile | Fehler (Code) | Richtig wäre | Problem |
|---|---|---|---|---|
| Q1 | Z. 74–75 | `if minimum is None:`<br>`continue` | Zeile(n) entfernen | Toter Zweig `if minimum is None`: set_min_stock speichert nie None. |
| Q2 | Z. 28 | `def receive(self, product, quantity, expiry_day, supplier=None):` | `def receive(self, product, quantity, expiry_day):` | Ungenutzter Parameter `supplier` täuscht vor, dass der Lieferant gespeichert wird. |
| Q3 | Z. 56 | `return quantity` | `return quantity - remaining` | Irreführender Rückgabewert: gibt die angefragte statt der tatsächlich gelieferten Menge zurück. |
| Q4 | Z. 84 | `result = 0` | Zeile(n) entfernen | Toter Wert: `result = 0` wird sofort überschrieben. |

## Köder (korrekter Code)

Diese Stellen sehen verdächtig aus, sind aber richtig. Meldet ein Judge sie als Bug, ist das ein Fehlalarm (−1).

| Zeile | Code | Warum richtig |
|---|---|---|
| Z. 36 | `if expiry_day >= today:` | `>=` ist richtig: am Ablauftag ist die Charge noch verkäuflich. |
| Z. 63 | `if batch[1] < today:` | `<` ist richtig: abgelaufen ist eine Charge erst nach ihrem Ablauftag. |
| Z. 76 | `if self.stock(product, today) < minimum:` | `<` ist richtig: genau der Mindestbestand löst keine Nachbestellung aus. |
