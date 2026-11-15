"""
Lagerverwaltung für verderbliche Ware. Tage werden als fortlaufende Zahlen angegeben.

Regeln:
- Ware kommt in Chargen an: Produkt, Menge (größer 0) und Ablauftag.
- Abgelaufen ist eine Charge erst nach ihrem Ablauftag; abgelaufene Chargen werden nie ausgeliefert.
- Ausgeliefert wird immer zuerst aus der Charge, die am frühesten abläuft.
- Eine Lieferung wird ganz oder gar nicht ausgeführt (sonst ValueError).
- remove_expired(today) entfernt alle abgelaufenen Chargen und gibt die entfernte Menge je Produkt zurück.
- reorder_list(today) nennt alphabetisch alle Produkte, deren verkäuflicher Bestand unter ihrem
  Mindestbestand liegt. Produkte ohne Mindestbestand werden nie nachbestellt.
- Jedes Lager hat seine eigenen Mindestbestände; sie lassen sich beim Anlegen übergeben.
- days_until_expiry(product, today) nennt, in wie vielen Tagen die nächste Charge des Produkts abläuft.
- value(product, today, unit_price) ist der Wert des verkäuflichen Bestands, auf den Cent gerundet.
"""


class Warehouse:
    def __init__(self, min_stock={}):
        self.batches = {}        # Produkt -> Liste von [Menge, Ablauftag]
        self.min_stock = min_stock      # Produkt -> Mindestbestand

    def set_min_stock(self, product, amount):
        if amount < 0:
            raise ValueError("Mindestbestand darf nicht negativ sein.")
        self.min_stock[product] = amount

    def receive(self, product, quantity, expiry_day, supplier=None):
        if quantity <= 0:
            raise ValueError("Menge muss positiv sein.")
        self.batches.setdefault(product, []).append([quantity, expiry_day])

    def stock(self, product, today):
        total = 0
        for quantity, expiry_day in self.batches.get(product, []):
            if expiry_day >= today:
                total += quantity
        return total

    def ship(self, product, quantity, today):
        if quantity <= 0:
            raise ValueError("Menge muss positiv sein.")
        batches = self.batches.get(product, [])
        available = sum(batch[0] for batch in batches)
        if available < quantity:
            raise ValueError("Nicht genug verkäuflicher Bestand.")
        batches.sort(key=lambda batch: batch[1], reverse=True)
        remaining = quantity
        for batch in batches:
            if batch[1] <= today:
                continue
            taken = min(batch[0], remaining)
            batch[0] -= taken
            remaining -= taken
        self.batches[product] = [batch for batch in batches if batch[0] > 0]
        return quantity

    def remove_expired(self, today):
        removed = {}
        for product, batches in self.batches.items():
            kept = []
            for batch in batches:
                if batch[1] < today:
                    removed[product] = removed.get(product, 0) + batch[0]
                else:
                    kept.append(batch)
            self.batches[product] = kept
        return removed

    def reorder_list(self, today):
        result = []
        for product in self.min_stock:
            minimum = self.min_stock[product]
            if minimum is None:
                continue
            if self.stock(product, today) < minimum:
                result.append(product)
        return sorted(result)

    def days_until_expiry(self, product, today):
        return max(batch[1] for batch in self.batches[product]) - today

    def value(self, product, today, unit_price):
        result = 0
        result = self.stock(product, today) * unit_price
        return round(result, 2)
