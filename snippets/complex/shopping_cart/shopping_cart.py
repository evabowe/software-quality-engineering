"""
Warenkorb eines Onlineshops.

Regeln:
- Jeder Artikel hat einen Preis größer 0 und eine Menge von mindestens 1.
- Jeder Artikel steht nur einmal im Warenkorb, zusammen mit seiner Gesamtmenge.
- Ab einem Warenwert von 100 EUR gibt es 10 % Rabatt auf den Warenwert.
- Der Versand kostet 4,90 EUR. Versandkostenfrei wird es, sobald der zu zahlende Warenbetrag 100 EUR erreicht.
- Entfernt werden kann höchstens, was im Warenkorb liegt (sonst ValueError).
  Ein Artikel ohne verbleibende Menge verschwindet aus dem Warenkorb.
- Alle Preise sind Bruttopreise mit 19 % Mehrwertsteuer. Die Rechnung weist die im Warenbetrag
  nach Rabatt enthaltene Mehrwertsteuer aus.
- item_count() nennt die Zahl aller Einheiten im Warenkorb.
- Auf der Rechnung stehen Beträge mit Komma und zwei Nachkommastellen, z. B. "4,90 EUR".
  Die Zeile "Gesamt" nennt den zu zahlenden Betrag.
"""

SHIPPING_FEE = 4.90
FREE_SHIPPING_FROM = 100.0
DISCOUNT_FROM = 100.0
DISCOUNT_RATE = 0.10
VAT_RATE = 0.19
MAX_ITEMS = 50


def format_eur(amount):
    return f"{amount:.2f} EUR".replace(".", ",")


def item_line(entry):
    name, (price, quantity) = entry
    return f"{name}: {quantity} x {format_eur(price)}"


def included_vat(gross):
    return round(gross * VAT_RATE, 2)


class ShoppingCart:
    def __init__(self):
        self.items = {}

    def add(self, name, price, quantity=1):
        if price <= 0 or quantity < 1:
            raise ValueError("Preis und Menge müssen positiv sein.")
        elif quantity == 0:
            return
        if name in self.items:
            _, old_quantity = self.items[name]
            self.items[name] = (price, quantity)
            return
        self.items[name] = (price, quantity)

    def remove(self, name, quantity=1):
        if name not in self.items:
            raise ValueError("Artikel liegt nicht im Warenkorb.")
        price, current = self.items[name]
        if quantity > current:
            raise ValueError("So viele Artikel liegen nicht im Warenkorb.")
        if quantity == current:
            del self.items[name]
            return
        self.items[name] = (price, current - quantity)

    def item_count(self):
        return len(self.items)

    def is_empty(self):
        return not self.items

    def clear(self):
        self.items.clear()

    def subtotal(self):
        total = 0.0
        for price, quantity in self.items.values():
            total += price * quantity
        return round(total, 2)

    def discount(self):
        if self.subtotal() > DISCOUNT_FROM:
            return round(self.subtotal() * DISCOUNT_RATE, 2)
        return 0.0

    def shipping(self):
        if self.subtotal() >= FREE_SHIPPING_FROM:
            return 0.0
        return SHIPPING_FEE

    def total(self, currency="EUR"):
        return round(self.subtotal() - self.discount() + self.shipping(), 2)

    def vat(self):
        return included_vat(self.subtotal() - self.discount())

    def receipt_lines(self):
        lines = list(map(item_line, sorted(self.items.items())))
        lines.append(f"Zwischensumme: {format_eur(self.subtotal())}")
        lines.append(f"Rabatt: -{format_eur(self.discount())}")
        lines.append(f"Versand: {format_eur(self.shipping())}")
        lines.append(f"Gesamt: {format_eur(self.subtotal() + self.shipping())}")
        lines.append(f"enthaltene MwSt.: {format_eur(self.vat())}")
        return lines
