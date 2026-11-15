import unittest

from library import Library


def library_with(*titles):
    library = Library()
    for title in titles:
        library.add_book(title)
    return library


class TestBorrow(unittest.TestCase):
    def test_borrow_available_book(self):
        library = library_with("Momo")
        library.borrow("Momo", "Anna", 1)
        self.assertEqual(library.loans["Momo"], ("Anna", 1))

    def test_borrow_lent_book_is_rejected(self):
        library = library_with("Momo")
        library.borrow("Momo", "Anna", 1)
        with self.assertRaises(ValueError):
            library.borrow("Momo", "Ben", 2)

    def test_borrow_unknown_book_is_rejected(self):
        library = library_with("Momo")
        with self.assertRaises(ValueError):
            library.borrow("Faust", "Anna", 1)

    def test_three_loans_are_allowed(self):
        library = library_with("A", "B", "C")
        for title in ("A", "B", "C"):
            library.borrow(title, "Anna", 1)
        self.assertEqual(library.count_loans("Anna"), 3)

    def test_fourth_loan_is_rejected(self):
        library = library_with("A", "B", "C", "D")
        for title in ("A", "B", "C"):
            library.borrow(title, "Anna", 1)
        with self.assertRaises(ValueError):
            library.borrow("D", "Anna", 1)
        self.assertIsNone(library.loans["D"])

    def test_high_open_fees_block_borrowing(self):
        library = library_with("Momo")
        library.fees["Anna"] = 5.50
        with self.assertRaises(ValueError):
            library.borrow("Momo", "Anna", 1)

    def test_open_fees_of_exactly_5_are_allowed(self):
        library = library_with("Momo")
        library.fees["Anna"] = 5.00
        library.borrow("Momo", "Anna", 1)
        self.assertEqual(library.loans["Momo"], ("Anna", 1))


class TestReservation(unittest.TestCase):
    def lent_to_ben_reserved_by_anna(self):
        library = library_with("Momo")
        library.borrow("Momo", "Ben", 1)
        library.reserve("Momo", "Anna")
        return library

    def test_available_book_cannot_be_reserved(self):
        library = library_with("Momo")
        with self.assertRaises(ValueError):
            library.reserve("Momo", "Anna")
        self.assertNotIn("Momo", library.reservations)

    def test_reserved_book_is_blocked_for_others(self):
        library = self.lent_to_ben_reserved_by_anna()
        library.give_back("Momo", 5)
        with self.assertRaises(ValueError):
            library.borrow("Momo", "Carl", 6)

    def test_reserving_person_can_borrow(self):
        library = self.lent_to_ben_reserved_by_anna()
        library.give_back("Momo", 5)
        library.borrow("Momo", "Anna", 6)
        self.assertEqual(library.loans["Momo"], ("Anna", 6))

    def test_reservation_ends_with_the_loan(self):
        library = self.lent_to_ben_reserved_by_anna()
        library.give_back("Momo", 5)
        library.borrow("Momo", "Anna", 6)
        library.give_back("Momo", 10)
        library.borrow("Momo", "Carl", 11)
        self.assertEqual(library.loans["Momo"], ("Carl", 11))

    def test_second_reservation_is_rejected(self):
        library = self.lent_to_ben_reserved_by_anna()
        with self.assertRaises(ValueError):
            library.reserve("Momo", "Carl")


class TestFees(unittest.TestCase):
    def test_return_on_time_costs_nothing(self):
        library = library_with("Momo")
        library.borrow("Momo", "Anna", 1)
        library.give_back("Momo", 15)
        self.assertEqual(library.fees.get("Anna", 0.0), 0.0)
        self.assertIsNone(library.loans["Momo"])

    def test_late_fee_per_day(self):
        library = library_with("Momo")
        library.borrow("Momo", "Anna", 1)
        library.give_back("Momo", 20)
        self.assertEqual(library.fees["Anna"], 2.50)

    def test_late_fee_is_capped_per_loan(self):
        library = library_with("Momo")
        library.borrow("Momo", "Anna", 1)
        library.give_back("Momo", 100)
        self.assertEqual(library.fees["Anna"], 10.0)

    def test_fees_of_several_loans_add_up(self):
        library = library_with("A", "B")
        library.borrow("A", "Anna", 1)
        library.borrow("B", "Anna", 1)
        library.give_back("A", 20)
        library.give_back("B", 17)
        self.assertEqual(library.fees["Anna"], 3.50)

    def test_return_of_book_not_lent_is_rejected(self):
        library = library_with("Momo")
        with self.assertRaises(ValueError):
            library.give_back("Momo", 3)

    def test_pay_reduces_open_fees(self):
        library = library_with("Momo")
        library.fees["Anna"] = 4.00
        library.pay("Anna", 1.50)
        self.assertEqual(library.fees["Anna"], 2.50)

    def test_paying_more_than_open_is_rejected(self):
        library = library_with("Momo")
        library.fees["Anna"] = 4.00
        with self.assertRaises(ValueError):
            library.pay("Anna", 5.00)
        self.assertEqual(library.fees["Anna"], 4.00)


class TestOverview(unittest.TestCase):
    def test_due_day_is_last_free_day(self):
        library = library_with("Momo")
        library.borrow("Momo", "Anna", 3)
        self.assertEqual(library.due_day("Momo"), 17)
        library.give_back("Momo", library.due_day("Momo"))
        self.assertEqual(library.fees.get("Anna", 0.0), 0.0)

    def test_member_summary_with_fees_to_the_cent(self):
        library = library_with("A", "B")
        library.borrow("A", "Anna", 1)
        library.give_back("A", 20)
        library.borrow("B", "Anna", 21)
        self.assertEqual(library.member_summary("Anna"), {"loans": 1, "reservations": 0, "fees": 2.5})


if __name__ == "__main__":
    unittest.main()
