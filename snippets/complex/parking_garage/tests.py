import unittest

from parking_garage import ParkingGarage, format_duration, parking_fee


class TestParkingFee(unittest.TestCase):
    def test_negative_duration_is_rejected(self):
        with self.assertRaises(ValueError):
            parking_fee(-1)

    def test_short_stay_is_free(self):
        self.assertEqual(parking_fee(10), 0.0)

    def test_exactly_30_minutes_is_free(self):
        self.assertEqual(parking_fee(30), 0.0)

    def test_started_hour_is_charged(self):
        self.assertEqual(parking_fee(31), 2.0)

    def test_second_started_hour_is_charged(self):
        self.assertEqual(parking_fee(61), 4.0)

    def test_full_hours(self):
        self.assertEqual(parking_fee(120), 4.0)

    def test_daily_cap(self):
        self.assertEqual(parking_fee(10 * 60), 15.0)

    def test_full_day_costs_daily_cap(self):
        self.assertEqual(parking_fee(24 * 60), 15.0)

    def test_full_day_plus_hours(self):
        self.assertEqual(parking_fee(24 * 60 + 120), 19.0)


class TestGarage(unittest.TestCase):
    def test_full_garage_rejects_entry(self):
        garage = ParkingGarage(capacity=2)
        garage.enter("A-1", 0)
        garage.enter("B-2", 0)
        with self.assertRaises(ValueError):
            garage.enter("C-3", 5)
        self.assertEqual(garage.free_spaces(), 0)

    def test_same_plate_twice_is_rejected(self):
        garage = ParkingGarage(capacity=5)
        garage.enter("A-1", 0)
        with self.assertRaises(ValueError):
            garage.enter("A-1", 10)

    def test_pay_returns_fee_and_counts_revenue(self):
        garage = ParkingGarage(capacity=5)
        garage.enter("A-1", 0)
        self.assertEqual(garage.pay("A-1", 120), 4.0)
        self.assertEqual(garage.revenue, 4.0)

    def test_lost_ticket(self):
        garage = ParkingGarage(capacity=5)
        garage.enter("A-1", 0)
        self.assertEqual(garage.pay("A-1", 60, ticket_lost=True), 25.0)

    def test_season_ticket_pays_nothing_and_exits_without_paying(self):
        garage = ParkingGarage(capacity=5, season_tickets=["D-4"])
        garage.enter("D-4", 0)
        self.assertEqual(garage.pay("D-4", 600), 0.0)
        garage.exit("D-4", 700)
        self.assertEqual(garage.free_spaces(), 5)

    def test_exit_without_paying_is_rejected(self):
        garage = ParkingGarage(capacity=5)
        garage.enter("A-1", 0)
        with self.assertRaises(ValueError):
            garage.exit("A-1", 60)

    def test_exit_exactly_15_minutes_after_paying(self):
        garage = ParkingGarage(capacity=5)
        garage.enter("A-1", 0)
        garage.pay("A-1", 100)
        garage.exit("A-1", 115)
        self.assertEqual(garage.free_spaces(), 5)

    def test_late_exit_is_rejected(self):
        garage = ParkingGarage(capacity=5)
        garage.enter("A-1", 0)
        garage.pay("A-1", 100)
        with self.assertRaises(ValueError):
            garage.exit("A-1", 116)

    def test_paying_again_charges_only_the_difference(self):
        garage = ParkingGarage(capacity=5)
        garage.enter("A-1", 0)
        garage.pay("A-1", 100)
        self.assertEqual(garage.pay("A-1", 130), 2.0)
        self.assertEqual(garage.revenue, 6.0)
        garage.exit("A-1", 140)

    def test_pay_for_unknown_car_is_rejected(self):
        garage = ParkingGarage(capacity=5)
        with self.assertRaises(ValueError):
            garage.pay("X-9", 10)


class TestReports(unittest.TestCase):
    def test_format_duration(self):
        self.assertEqual(format_duration(125), "2 h 05 min")
        self.assertEqual(format_duration(45), "0 h 45 min")

    def test_occupancy_in_percent(self):
        garage = ParkingGarage(capacity=4)
        garage.enter("A-1", 0)
        garage.enter("B-2", 0)
        self.assertEqual(garage.occupancy(), 50.0)

    def test_receipt_shows_duration_and_fee_so_far(self):
        garage = ParkingGarage(capacity=4)
        garage.enter("A-1", 10)
        receipt = garage.receipt("A-1", 71)
        self.assertEqual(receipt["minutes"], 61)
        self.assertEqual(receipt["duration"], "1 h 01 min")
        self.assertEqual(receipt["fee"], 4.0)


if __name__ == "__main__":
    unittest.main()
