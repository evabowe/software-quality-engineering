import unittest

from warehouse import Warehouse


class TestReceiveAndStock(unittest.TestCase):
    def test_receive_non_positive_quantity_is_rejected(self):
        warehouse = Warehouse()
        with self.assertRaises(ValueError):
            warehouse.receive("Milch", 0, 10)

    def test_stock_sums_sellable_batches(self):
        warehouse = Warehouse()
        warehouse.receive("Milch", 5, 10)
        warehouse.receive("Milch", 3, 12)
        self.assertEqual(warehouse.stock("Milch", 1), 8)

    def test_stock_includes_batch_expiring_today_and_excludes_expired(self):
        warehouse = Warehouse()
        warehouse.receive("Milch", 5, 10)
        warehouse.receive("Milch", 3, 9)
        self.assertEqual(warehouse.stock("Milch", 10), 5)

    def test_negative_minimum_is_rejected(self):
        warehouse = Warehouse()
        with self.assertRaises(ValueError):
            warehouse.set_min_stock("Milch", -1)


class TestShip(unittest.TestCase):
    def test_ship_reduces_stock(self):
        warehouse = Warehouse()
        warehouse.receive("Milch", 5, 10)
        warehouse.ship("Milch", 2, 1)
        self.assertEqual(warehouse.stock("Milch", 1), 3)

    def test_ship_takes_earliest_expiry_first(self):
        warehouse = Warehouse()
        warehouse.receive("Milch", 5, 20)
        warehouse.receive("Milch", 5, 10)
        warehouse.ship("Milch", 3, 1)
        # Ab Tag 11 ist nur noch die Charge mit Ablauftag 20 verkäuflich – sie muss unangetastet sein.
        self.assertEqual(warehouse.stock("Milch", 11), 5)

    def test_ship_uses_batch_expiring_today(self):
        warehouse = Warehouse()
        warehouse.receive("Milch", 4, 5)
        warehouse.ship("Milch", 4, 5)
        self.assertEqual(warehouse.stock("Milch", 5), 0)

    def test_ship_more_than_stock_is_rejected(self):
        warehouse = Warehouse()
        warehouse.receive("Milch", 2, 10)
        with self.assertRaises(ValueError):
            warehouse.ship("Milch", 3, 1)
        self.assertEqual(warehouse.stock("Milch", 1), 2)

    def test_expired_stock_does_not_count_and_nothing_is_shipped(self):
        warehouse = Warehouse()
        warehouse.receive("Milch", 3, 2)
        warehouse.receive("Milch", 2, 10)
        with self.assertRaises(ValueError):
            warehouse.ship("Milch", 4, 5)
        self.assertEqual(warehouse.stock("Milch", 5), 2)

    def test_ship_non_positive_quantity_is_rejected(self):
        warehouse = Warehouse()
        warehouse.receive("Milch", 2, 10)
        with self.assertRaises(ValueError):
            warehouse.ship("Milch", 0, 1)


class TestExpiredAndReorder(unittest.TestCase):
    def test_remove_expired_returns_removed_quantities(self):
        warehouse = Warehouse()
        warehouse.receive("Milch", 3, 2)
        warehouse.receive("Milch", 2, 10)
        warehouse.receive("Käse", 4, 1)
        self.assertEqual(warehouse.remove_expired(5), {"Milch": 3, "Käse": 4})
        self.assertEqual(warehouse.stock("Milch", 5), 2)

    def test_remove_expired_keeps_batch_expiring_today(self):
        warehouse = Warehouse()
        warehouse.receive("Milch", 3, 5)
        self.assertEqual(warehouse.remove_expired(5), {})

    def test_reorder_list_is_sorted_and_only_below_minimum(self):
        warehouse = Warehouse()
        warehouse.receive("Milch", 2, 10)
        warehouse.receive("Brot", 10, 10)
        warehouse.set_min_stock("Milch", 5)
        warehouse.set_min_stock("Brot", 5)
        warehouse.set_min_stock("Butter", 1)
        self.assertEqual(warehouse.reorder_list(1), ["Butter", "Milch"])

    def test_stock_exactly_at_minimum_is_not_reordered(self):
        warehouse = Warehouse()
        warehouse.receive("Milch", 5, 10)
        warehouse.set_min_stock("Milch", 5)
        self.assertEqual(warehouse.reorder_list(1), [])

    def test_products_without_minimum_are_never_reordered(self):
        warehouse = Warehouse()
        warehouse.receive("Milch", 1, 10)
        self.assertEqual(warehouse.reorder_list(1), [])

    def test_expired_stock_triggers_reorder(self):
        warehouse = Warehouse()
        warehouse.receive("Milch", 10, 3)
        warehouse.set_min_stock("Milch", 5)
        self.assertEqual(warehouse.reorder_list(4), ["Milch"])


class TestSeveralWarehouses(unittest.TestCase):
    def test_minimums_are_per_warehouse(self):
        first = Warehouse()
        first.set_min_stock("Mehl", 5)
        second = Warehouse()
        self.assertEqual(second.reorder_list(1), [])

    def test_minimums_can_be_passed_on_creation(self):
        warehouse = Warehouse({"Brot": 3})
        self.assertEqual(warehouse.reorder_list(1), ["Brot"])


class TestOverview(unittest.TestCase):
    def test_days_until_next_expiry(self):
        warehouse = Warehouse()
        warehouse.receive("Milch", 5, 20)
        warehouse.receive("Milch", 5, 10)
        self.assertEqual(warehouse.days_until_expiry("Milch", 4), 6)

    def test_value_of_sellable_stock(self):
        warehouse = Warehouse()
        warehouse.receive("Milch", 3, 10)
        warehouse.receive("Milch", 2, 1)
        self.assertEqual(warehouse.value("Milch", 5, 1.15), 3.45)


if __name__ == "__main__":
    unittest.main()
