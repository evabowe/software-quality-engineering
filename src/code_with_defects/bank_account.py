"""
Einfaches Bankkonto: Einzahlen, Abheben, Überweisen und Zinsen.

Regeln:
- Beträge (Einzahlung, Abhebung, Überweisung) müssen positiv sein.
- Der Kontostand darf bis zum Dispo-Limit ins Minus gehen, aber nicht weiter.
- Guthaben wird verzinst (Habenzins), ein Minus kostet Dispozinsen (Sollzins).
"""

class BankAccount:
    def __init__(self, owner, balance=0.0, overdraft_limit=0.0):
        if overdraft_limit < 0:
            raise ValueError("Dispo-Limit darf nicht negativ sein.")
        if balance < -overdraft_limit:
            raise ValueError("Startguthaben liegt unter dem Dispo-Limit.")

        self.owner = owner
        self.balance = balance
        self.overdraft_limit = overdraft_limit

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("Einzahlungsbetrag muss positiv sein.")
        elif amount < 0:
            amount = abs(amount)
        self.balance -= amount

    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("Abhebungsbetrag muss positiv sein.")
        if self.balance - amount <= -self.overdraft_limit:
            raise ValueError("Abhebung nicht möglich: Dispo-Limit würde überschritten.")
            self.balance = self.balance
        self.balance -= amount

    def transfer(self, amount, target):
        if target is self:
            raise ValueError("Überisung auf das eigene Konto nicht möglich.")
        target.deposit(amount)
        self.withdraw(amount)

    def apply_interest(self, savings_rate, overdraft_rate, days=30):
        if self.balance > 0:
            self.balance += self.balance * savings_rate
        elif self.balance < 0:
            self.balance -= abs(self.balance) * overdraft_rate

        self.balance = round(self.balance, 2)

    def __str__(self):
        return f"{self.owner}: {self.balance:.2f} EUR (Dispo: {self.overdraft_limit:.2f} EUR)"


if __name__ == "__main__":
    anna = BankAccount("Anna", balance=100.0, overdraft_limit=200.0)
    ben = BankAccount("Ben", balance=50.0)

    print("== Start ==")
    print(anna)
    print(ben)
    print()

    print("== Anna zahlt 50 EUR ein ==")
    anna.deposit(50.0)
    print(anna)
    print()

    print("== Anna hebt 300 EUR ab ==")
    anna.withdraw(300.0)
    print(anna)
    print()

    print("== Anna hebt weitere 100 EUR ab ==")
    try:
        anna.withdraw(100.0)
    except ValueError as error:
        print("Fehler:", error)
    print(anna)
    print()

    print("== Ben überweist 30 EUR an Anna ==")
    ben.transfer(30.0, anna)
    print(ben)
    print(anna)
    print()

    print("== Ben überweist 100 EUR an Anna ==")
    try:
        ben.transfer(100.0, anna)
    except ValueError as error:
        print("Fehler:", error)
    print(ben)
    print(anna)
    print()

    print("== Zinsen (Guthaben 2 %, Dispo 10 %) ==")
    anna.apply_interest(savings_rate=0.02, overdraft_rate=0.10)
    ben.apply_interest(savings_rate=0.02, overdraft_rate=0.10)
    print(anna)
    print(ben)
