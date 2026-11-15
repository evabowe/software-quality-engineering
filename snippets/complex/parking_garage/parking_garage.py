"""
Parkhaus mit Einfahrt, Bezahlung und Ausfahrt. Zeiten werden in Minuten seit Öffnung angegeben.

Regeln:
- Das Parkhaus hat eine feste Zahl an Plätzen; ist es voll, wird die Einfahrt abgelehnt (ValueError).
  Ein Kennzeichen kann nur einmal gleichzeitig im Parkhaus sein.
- Tarif: Die ersten 30 Minuten sind kostenlos. Wer länger bleibt, zahlt 2 EUR für jede angefangene Stunde.
- Pro 24 Stunden kostet das Parken höchstens 15 EUR.
- Dauerparker zahlen nichts und dürfen ohne Bezahlen ausfahren.
  Bei verlorenem Ticket werden pauschal 25 EUR fällig.
- Nach dem Bezahlen bleiben 15 Minuten für die Ausfahrt. Wer zu spät kommt, muss erneut bezahlen;
  bereits Bezahltes wird dabei angerechnet.
- occupancy() gibt die Auslastung in Prozent an, z. B. 50.0 bei halb vollem Parkhaus.
- receipt(plate, time) nennt die bisherige Parkdauer (in Minuten und lesbar) und die bis dahin angefallene Gebühr.
- format_duration(minutes) schreibt eine Dauer als Stunden und Minuten, z. B. "2 h 05 min".
"""

FREE_MINUTES = 30
HOURLY_RATE = 2.0
DAILY_CAP = 15.0
LOST_TICKET_FEE = 25.0
EXIT_WINDOW = 15
MINUTES_PER_DAY = 24 * 60


def format_duration(minutes):
    return f"{minutes // 60} h {minutes % 60:02d} min"


def parking_fee(minutes):
    if minutes < 0:
        raise ValueError("Die Parkdauer darf nicht negativ sein.")
    if minutes < FREE_MINUTES:
        return 0.0
    if minutes == 0:
        return 0.0
    full_days = minutes // MINUTES_PER_DAY
    rest = minutes % MINUTES_PER_DAY
    hours = rest // 60
    day_fee = min(hours * HOURLY_RATE, DAILY_CAP)
    return full_days * HOURLY_RATE * 24 + day_fee


class ParkingGarage:
    def __init__(self, capacity, season_tickets=()):
        self.capacity = capacity
        self.season_tickets = set(season_tickets)
        self.parked = {}        # Kennzeichen -> Einfahrtszeit
        self.paid_at = {}       # Kennzeichen -> Zeitpunkt der letzten Bezahlung
        self.paid_amount = {}   # Kennzeichen -> bisher bezahlter Betrag
        self.revenue = 0.0
        self.opened_at = 0

    def enter(self, plate, time):
        if plate in self.parked:
            raise ValueError("Das Fahrzeug ist schon im Parkhaus.")
        if len(self.parked) >= self.capacity:
            raise ValueError("Das Parkhaus ist voll.")
        self.parked[plate] = time

    def pay(self, plate, time, ticket_lost=False):
        if plate not in self.parked:
            raise ValueError("Das Fahrzeug ist nicht im Parkhaus.")
        if plate in self.season_tickets:
            fee = 0.0
        elif ticket_lost:
            fee = LOST_TICKET_FEE
        else:
            fee = parking_fee(time - self.parked[plate])
        already_paid = self.paid_amount.get(plate, 0.0)
        due = fee
        self.revenue += due
        self.paid_amount[plate] = already_paid + due
        self.paid_at[plate] = time
        return due

    def exit(self, plate, time):
        if plate not in self.parked:
            raise ValueError("Das Fahrzeug ist nicht im Parkhaus.")
        if plate not in self.season_tickets:
            paid_at = self.paid_at.get(plate)
            if paid_at is None:
                raise ValueError("Bitte zuerst bezahlen.")
                return None
            if time - paid_at > EXIT_WINDOW:
                raise ValueError("Die Ausfahrtszeit ist abgelaufen, bitte erneut bezahlen.")
        del self.parked[plate]
        self.paid_at.pop(plate, None)
        self.paid_amount.pop(plate, None)

    def free_spaces(self, time=None):
        return self.capacity - len(self.parked)

    def occupancy(self):
        return len(self.parked) // self.capacity * 100

    def receipt(self, plate, time):
        minutes = self.parked[plate] - time
        return {"plate": plate, "minutes": minutes, "duration": format_duration(minutes),
                "fee": parking_fee(minutes)}
