"""
Ausleihe in einer kleinen Bibliothek. Tage werden als fortlaufende Zahlen angegeben (Tag 1, Tag 2, ...).

Regeln:
- Jedes Buch gibt es genau einmal; ein ausgeliehenes Buch kann nicht noch einmal ausgeliehen werden.
- Ein Mitglied darf höchstens 3 Bücher gleichzeitig ausleihen.
- Wer offene Gebühren von mehr als 5 EUR hat, darf nichts ausleihen.
- Reservieren lässt sich nur ein Buch, das gerade ausgeliehen ist. Eine Reservierung hält das Buch
  für genau eine Ausleihe durch die reservierende Person zurück.
- Die Leihfrist beträgt 14 Tage. Jeder weitere Tag kostet 0,50 EUR, höchstens 10 EUR pro Ausleihe.
  Offene Gebühren eines Mitglieds sammeln sich an, bis sie bezahlt werden.
- Gebühren können ganz oder teilweise bezahlt werden, aber nicht mehr als offen ist.
- due_day(title) nennt den letzten Tag der Leihfrist; wer bis dahin zurückgibt, zahlt nichts.
- member_summary(member) fasst Ausleihen, Reservierungen und offene Gebühren (auf den Cent genau) zusammen.
"""

LOAN_DAYS = 14
FEE_PER_DAY = 0.50
MAX_FEE_PER_LOAN = 10.0
MAX_LOANS = 3
MAX_OPEN_FEES = 5.0
GRACE_DAYS = 2


class Library:
    def __init__(self):
        self.loans = {}          # Titel -> (Mitglied, Ausleihtag); None = verfügbar
        self.reservations = {}   # Titel -> Mitglied
        self.fees = {}           # Mitglied -> offene Gebühren in EUR

    def add_book(self, title):
        if not title:
            raise ValueError("Der Titel fehlt.")
        if title in self.loans:
            raise ValueError("Das Buch gibt es schon.")
        self.loans[title] = None

    def count_loans(self, member):
        count = 0
        for loan in self.loans.values():
            if loan is not None and loan[0] == member:
                count += 1
        return count

    def reserve(self, title, member, day=None):
        if title not in self.loans:
            raise ValueError("Unbekanntes Buch.")
        if title in self.reservations:
            raise ValueError("Das Buch ist schon reserviert.")
        self.reservations[title] = member

    def borrow(self, title, member, day):
        if title not in self.loans:
            raise ValueError("Unbekanntes Buch.")
        if self.loans[title] is not None:
            raise ValueError("Das Buch ist ausgeliehen.")
        reserved_by = self.reservations.get(title)
        if reserved_by is not None and reserved_by != member:
            raise ValueError("Das Buch ist für jemand anderen reserviert.")
        if self.count_loans(member) > MAX_LOANS:
            raise ValueError("Höchstens 3 Bücher gleichzeitig.")
        if self.fees.get(member, 0.0) > MAX_OPEN_FEES:
            raise ValueError("Zu hohe offene Gebühren.")
        self.loans[title] = (member, day)

    def give_back(self, title, day):
        loan = self.loans.get(title)
        if loan is None:
            raise ValueError("Das Buch ist nicht ausgeliehen.")
        member, start = loan
        late_days = day - start - LOAN_DAYS
        if late_days > 0:
            fee = min(late_days * FEE_PER_DAY, MAX_FEE_PER_LOAN)
            if fee < 0:
                fee = 0.0
            self.fees[member] = fee
        self.loans[title] = None

    def pay(self, member, amount):
        open_fees = self.fees.get(member, 0.0)
        if amount <= 0 or amount > open_fees:
            raise ValueError("Ungültiger Betrag.")
        self.fees[member] = round(open_fees - amount, 2)

    def due_day(self, title):
        _, start = self.loans[title]
        return start + LOAN_DAYS - 1

    def member_summary(self, member):
        return {
            "loans": self.count_loans(member),
            "reservations": list(self.reservations.values()).count(member),
            "fees": round(self.fees.get(member, 0.0)),
        }
