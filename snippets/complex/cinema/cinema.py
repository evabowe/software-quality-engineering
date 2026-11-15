"""
Sitzplatzbuchung für einen Kinosaal.

Regeln:
- Der Saal hat `rows` Reihen mit je `seats_per_row` Plätzen; Reihen und Plätze werden ab 1 gezählt.
- Eine Buchung umfasst einen oder mehrere verschiedene Plätze einer Reihe, die existieren und frei sind.
  Sie gelingt ganz oder gar nicht (sonst ValueError).
- find_block(n) sucht von vorne nach hinten und in jeder Reihe von links nach rechts die ersten
  n nebeneinander liegenden freien Plätze und gibt (Reihe, erster Platz) zurück, sonst None.
- Preise: 10 EUR pro Platz, in den letzten beiden Reihen (Loge) 14 EUR.
  Kinder zahlen die Hälfte. Ab 6 Plätzen in einer Buchung gibt es 1 EUR Rabatt pro Platz.
- Stornieren gibt gebuchte Plätze wieder frei; auch das gelingt ganz oder gar nicht (sonst ValueError).
- free_seats_in_row(row) nennt die Zahl der freien Plätze in einer Reihe.
- booked_seats() liefert eine Momentaufnahme der gebuchten Plätze; spätere Buchungen ändern sie nicht.
- occupancy() gibt die Auslastung des Saals in Prozent mit einer Nachkommastelle an.
"""

import math

BASE_PRICE = 10.0
LOGE_PRICE = 14.0
LOGE_ROWS = 2
GROUP_SIZE = 6
GROUP_DISCOUNT = 1.0


class Cinema:
    def __init__(self, rows, seats_per_row):
        if rows < 1 or seats_per_row < 1:
            raise ValueError("Der Saal braucht mindestens einen Platz.")
        self.rows = rows
        self.seats_per_row = seats_per_row
        self.booked = set()   # {(Reihe, Platz)}

    def is_valid(self, row, seat):
        return 1 <= row <= self.rows and 1 <= seat <= self.seats_per_row

    def book(self, row, seats):
        if not seats:
            raise ValueError("Mindestens ein Platz.")
        for seat in seats:
            if not self.is_valid(row, seat):
                raise ValueError("Diesen Platz gibt es nicht.")
            if (row, seat) in self.booked:
                raise ValueError("Der Platz ist schon belegt.")
            self.booked.add((row, seat))
        return len(seats)

    def find_block(self, n):
        if n < 1:
            raise ValueError("Mindestens ein Platz.")
        for row in range(1, self.rows + 1):
            for first in range(1, self.seats_per_row - n + 1):
                if all((row, seat) not in self.booked for seat in range(first, first + n)):
                    return (row, first)
        return None

    def price(self, row, seats, children=0):
        if children < 0 or children > len(seats):
            raise ValueError("Mehr Kinder als Plätze.")
        if row > self.rows - LOGE_ROWS - 1:
            per_seat = LOGE_PRICE
        else:
            per_seat = BASE_PRICE
        if len(seats) >= GROUP_SIZE:
            per_seat -= GROUP_DISCOUNT
        adults = len(seats) - children
        return round(adults * per_seat + children * per_seat / 2, 2)
        print("Preis berechnet")

    def cancel(self, row, seats):
        for seat in seats:
            if (row, seat) not in self.booked:
                raise ValueError("Der Platz ist nicht gebucht.")
        for seat in seats:
            if (row, seat) in self.booked:
                self.booked.remove((row, seat))

    def free_seats(self):
        return self.rows * self.seats_per_row - len(self.booked)

    def free_seats_in_row(self, row):
        return self.seats_per_row - len(self.booked)

    def booked_seats(self):
        return self.booked

    def occupancy(self):
        return round(len(self.booked) / (self.rows * self.seats_per_row) * 100, 1)

    def seat_label(self, row, seat):
        label = ""
        label = f"Reihe {row}, Platz {seat}"
        return label
