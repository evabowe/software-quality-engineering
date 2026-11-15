import unittest

from cinema import Cinema


class TestBooking(unittest.TestCase):
    def test_hall_without_seats_is_rejected(self):
        with self.assertRaises(ValueError):
            Cinema(0, 10)

    def test_book_free_seats(self):
        cinema = Cinema(5, 10)
        self.assertEqual(cinema.book(1, [3, 4]), 2)
        self.assertEqual(cinema.free_seats(), 48)

    def test_book_taken_seat_is_rejected(self):
        cinema = Cinema(5, 10)
        cinema.book(1, [3])
        with self.assertRaises(ValueError):
            cinema.book(1, [3])

    def test_book_invalid_seat_is_rejected(self):
        cinema = Cinema(5, 10)
        with self.assertRaises(ValueError):
            cinema.book(6, [1])
        self.assertEqual(cinema.free_seats(), 50)

    def test_failed_booking_books_nothing(self):
        cinema = Cinema(5, 10)
        cinema.book(1, [3])
        with self.assertRaises(ValueError):
            cinema.book(1, [1, 2, 3])
        self.assertEqual(cinema.free_seats(), 49)

    def test_seat_twice_in_one_booking_is_rejected(self):
        cinema = Cinema(5, 10)
        with self.assertRaises(ValueError):
            cinema.book(1, [3, 3])
        self.assertEqual(cinema.free_seats(), 50)

    def test_last_row_and_last_seat_exist(self):
        cinema = Cinema(5, 10)
        cinema.book(5, [10])
        self.assertEqual(cinema.free_seats(), 49)

    def test_booking_with_invalid_last_seat_books_nothing(self):
        cinema = Cinema(5, 10)
        with self.assertRaises(ValueError):
            cinema.book(2, [9, 10, 11])
        self.assertEqual(cinema.free_seats(), 50)


class TestFindBlock(unittest.TestCase):
    def test_empty_hall_starts_front_left(self):
        cinema = Cinema(5, 10)
        self.assertEqual(cinema.find_block(4), (1, 1))

    def test_block_skips_taken_seats(self):
        cinema = Cinema(5, 10)
        cinema.book(1, [2])
        self.assertEqual(cinema.find_block(3), (1, 3))

    def test_block_at_end_of_row(self):
        cinema = Cinema(2, 5)
        cinema.book(1, [1, 2])
        self.assertEqual(cinema.find_block(3), (1, 3))

    def test_block_continues_in_next_row(self):
        cinema = Cinema(2, 5)
        cinema.book(1, [3])
        self.assertEqual(cinema.find_block(3), (2, 1))

    def test_no_block_returns_none(self):
        cinema = Cinema(1, 4)
        cinema.book(1, [2])
        self.assertIsNone(cinema.find_block(3))

    def test_block_of_zero_is_rejected(self):
        cinema = Cinema(1, 4)
        with self.assertRaises(ValueError):
            cinema.find_block(0)


class TestPrice(unittest.TestCase):
    def test_normal_price(self):
        cinema = Cinema(10, 12)
        self.assertEqual(cinema.price(5, [1, 2]), 20.0)

    def test_loge_in_last_two_rows(self):
        cinema = Cinema(10, 12)
        self.assertEqual(cinema.price(9, [1]), 14.0)
        self.assertEqual(cinema.price(10, [1]), 14.0)

    def test_row_before_loge_has_normal_price(self):
        cinema = Cinema(10, 12)
        self.assertEqual(cinema.price(8, [1]), 10.0)

    def test_children_pay_half(self):
        cinema = Cinema(10, 12)
        self.assertEqual(cinema.price(5, [1, 2], children=1), 15.0)

    def test_group_discount_from_six_seats(self):
        cinema = Cinema(10, 12)
        self.assertEqual(cinema.price(1, [1, 2, 3, 4, 5, 6]), 54.0)

    def test_more_children_than_seats_is_rejected(self):
        cinema = Cinema(10, 12)
        with self.assertRaises(ValueError):
            cinema.price(1, [1], children=2)


class TestCancel(unittest.TestCase):
    def test_cancel_frees_seats(self):
        cinema = Cinema(5, 10)
        cinema.book(1, [3, 4])
        cinema.cancel(1, [3, 4])
        self.assertEqual(cinema.free_seats(), 50)

    def test_cancel_of_unbooked_seat_cancels_nothing(self):
        cinema = Cinema(5, 10)
        cinema.book(1, [3])
        with self.assertRaises(ValueError):
            cinema.cancel(1, [3, 4])
        self.assertEqual(cinema.free_seats(), 49)


class TestOverview(unittest.TestCase):
    def test_free_seats_in_row_counts_only_that_row(self):
        cinema = Cinema(5, 10)
        cinema.book(1, [1, 2])
        cinema.book(2, [1])
        self.assertEqual(cinema.free_seats_in_row(2), 9)

    def test_booked_seats_is_a_snapshot(self):
        cinema = Cinema(5, 10)
        cinema.book(1, [1])
        snapshot = cinema.booked_seats()
        cinema.book(2, [1])
        self.assertEqual(len(snapshot), 1)

    def test_occupancy_in_percent(self):
        cinema = Cinema(3, 10)
        cinema.book(1, [1, 2, 3, 4])
        self.assertEqual(cinema.occupancy(), 13.3)

    def test_seat_label(self):
        cinema = Cinema(3, 10)
        self.assertEqual(cinema.seat_label(2, 7), "Reihe 2, Platz 7")


if __name__ == "__main__":
    unittest.main()
