# shopping_cart – Lösung (CL1, complexipy 10)

> **Achtung, Lösung:** Diese Datei beschreibt die eingebauten Defekte. Sie wird im Hands-on-Notebook nie angezeigt und darf nicht in einen Judge-Prompt gelangen.

## Tests ausführen

Im Terminal aus diesem Ordner heraus: `python -m pytest tests.py`. Die Tests schlagen absichtlich fehl (siehe unten). Die Projekt-Testsuite prüft automatisch, dass sie auf dem korrigierten Code (alle Korrekturen aus `meta.yaml`) grün laufen (`tests/test_ground_truth.py`).

## Eingebaute Fehler

### shopping_cart.py – semantische Fehler

| # | Zeile | Fehler (Code) | Richtig wäre | Auswirkung |
|---|---|---|---|---|
| B1 | Z. 50 | `self.items[name] = (price, quantity)` | `self.items[name] = (price, old_quantity + quantity)` | Erneutes Hinzufügen überschreibt die Menge, statt sie zu erhöhen. |
| B2 | Z. 81 | `if self.subtotal() > DISCOUNT_FROM:` | `if self.subtotal() >= DISCOUNT_FROM:` | Rabatt erst über 100 EUR statt ab 100 EUR (`>` statt `>=`). |
| B3 | Z. 86 | `if self.subtotal() >= FREE_SHIPPING_FROM:` | `if self.subtotal() - self.discount() >= FREE_SHIPPING_FROM:` | Versandfreiheit wird am Warenwert vor Rabatt gemessen statt nach Rabatt. |
| B4 | Z. 36 | `return round(gross * VAT_RATE, 2)` | `return round(gross - gross / (1 + VAT_RATE), 2)` | Die enthaltene Mehrwertsteuer wird aufgeschlagen statt aus dem Bruttobetrag herausgerechnet. |
| B5 | Z. 66 | `return len(self.items)` | `return sum(quantity for _, quantity in self.items.values())` | Item_count zählt verschiedene Artikel statt aller Einheiten. |
| B6 | Z. 101 | `lines.append(f"Gesamt: {format_eur(self.subtotal() + self.shipping())}")` | `lines.append(f"Gesamt: {format_eur(self.total())}")` | Die Zeile „Gesamt“ rechnet selbst und vergisst den Rabatt, statt total() zu verwenden. |

Fehlschlagende Tests (8 von 23):

| Test | Ursache |
|---|---|
| `TestAdd::test_add_same_item_increases_quantity` | Fehler B1 |
| `TestPrices::test_discount_from_exactly_100` | Fehler B2 |
| `TestPrices::test_shipping_charged_if_discounted_value_below_100` | Fehler B3 |
| `TestPrices::test_total_combines_discount_and_shipping` | Fehler B3 (Versand fehlt in der Summe) |
| `TestReceipt::test_included_vat` | Fehler B4 |
| `TestReceipt::test_vat_of_cart_after_discount` | Fehler B4 |
| `TestReceipt::test_item_count_counts_all_units` | Fehler B5 |
| `TestReceipt::test_receipt_total_is_amount_due` | Fehler B6 (zusätzlich B3) |

### shopping_cart.py – programmatische Fehler (Code-Qualität)

Diese Fehler ändern das Verhalten nicht und lassen keinen Test fehlschlagen.

| # | Zeile | Fehler (Code) | Richtig wäre | Problem |
|---|---|---|---|---|
| Q1 | Z. 46–47 | `elif quantity == 0:`<br>`return` | Zeile(n) entfernen | Toter Zweig `elif quantity == 0`: Menge 0 löst schon vorher den Fehler aus. |
| Q2 | Z. 90 | `def total(self, currency="EUR"):` | `def total(self):` | Ungenutzter Parameter `currency` täuscht eine Währungsumrechnung vor. |
| Q3 | Z. 23 | `MAX_ITEMS = 50` | Zeile(n) entfernen | Ungenutzte Konstante `MAX_ITEMS` täuscht eine Obergrenze vor, die nirgends geprüft wird. |

## Köder (korrekter Code)

Diese Stellen sehen verdächtig aus, sind aber richtig. Meldet ein Judge sie als Bug, ist das ein Fehlalarm (−1).

| Zeile | Code | Warum richtig |
|---|---|---|
| Z. 27 | `return f"{amount:.2f} EUR".replace(".", ",")` | Das Komma statt des Punkts ist gewollt (deutsche Schreibweise). |
| Z. 58 | `if quantity > current:` | `>` ist richtig: genau alle Einheiten zu entfernen ist erlaubt. |
| Z. 44 | `if price <= 0 or quantity < 1:` | Die Grenzen sind richtig: Preis 0 und Menge 0 sind ungültig. |
