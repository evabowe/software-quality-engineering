import unittest

from shopping_cart import ShoppingCart, format_eur, included_vat


class TestAdd(unittest.TestCase):
    def test_add_new_item(self):
        cart = ShoppingCart()
        cart.add("Buch", 12.50, 2)
        self.assertEqual(cart.items["Buch"], (12.50, 2))

    def test_add_same_item_increases_quantity(self):
        cart = ShoppingCart()
        cart.add("Buch", 12.50, 2)
        cart.add("Buch", 12.50, 3)
        self.assertEqual(cart.items["Buch"], (12.50, 5))

    def test_add_zero_price_is_rejected(self):
        cart = ShoppingCart()
        with self.assertRaises(ValueError):
            cart.add("Buch", 0.0)
        self.assertEqual(cart.items, {})

    def test_add_zero_quantity_is_rejected(self):
        cart = ShoppingCart()
        with self.assertRaises(ValueError):
            cart.add("Buch", 12.50, 0)
        self.assertEqual(cart.items, {})


class TestRemove(unittest.TestCase):
    def test_remove_part_of_quantity(self):
        cart = ShoppingCart()
        cart.add("Stift", 1.20, 5)
        cart.remove("Stift", 2)
        self.assertEqual(cart.items["Stift"], (1.20, 3))

    def test_remove_last_unit_deletes_item(self):
        cart = ShoppingCart()
        cart.add("Stift", 1.20, 2)
        cart.remove("Stift", 2)
        self.assertNotIn("Stift", cart.items)

    def test_remove_too_many_is_rejected_and_cart_unchanged(self):
        cart = ShoppingCart()
        cart.add("Stift", 1.20, 2)
        with self.assertRaises(ValueError):
            cart.remove("Stift", 3)
        self.assertEqual(cart.items["Stift"], (1.20, 2))

    def test_remove_unknown_item_is_rejected(self):
        cart = ShoppingCart()
        with self.assertRaises(ValueError):
            cart.remove("Heft")


class TestPrices(unittest.TestCase):
    def test_subtotal_sums_all_items(self):
        cart = ShoppingCart()
        cart.add("Buch", 12.50, 2)
        cart.add("Stift", 1.20, 3)
        self.assertEqual(cart.subtotal(), 28.60)

    def test_no_discount_below_100(self):
        cart = ShoppingCart()
        cart.add("Jacke", 99.99)
        self.assertEqual(cart.discount(), 0.0)

    def test_discount_from_exactly_100(self):
        cart = ShoppingCart()
        cart.add("Jacke", 100.00)
        self.assertEqual(cart.discount(), 10.0)

    def test_shipping_below_threshold(self):
        cart = ShoppingCart()
        cart.add("Buch", 30.00)
        self.assertEqual(cart.shipping(), 4.90)

    def test_free_shipping_from_100_after_discount(self):
        cart = ShoppingCart()
        cart.add("Mantel", 120.00)
        self.assertEqual(cart.shipping(), 0.0)

    def test_shipping_charged_if_discounted_value_below_100(self):
        cart = ShoppingCart()
        cart.add("Jacke", 105.00)
        self.assertEqual(cart.shipping(), 4.90)

    def test_total_combines_discount_and_shipping(self):
        cart = ShoppingCart()
        cart.add("Jacke", 105.00)
        self.assertEqual(cart.total(), 99.40)

    def test_total_without_discount(self):
        cart = ShoppingCart()
        cart.add("Buch", 30.00)
        self.assertEqual(cart.total(), 34.90)


class TestReceipt(unittest.TestCase):
    def test_format_eur(self):
        self.assertEqual(format_eur(4.9), "4,90 EUR")
        self.assertEqual(format_eur(1234.5), "1234,50 EUR")

    def test_included_vat(self):
        self.assertEqual(included_vat(119.0), 19.0)

    def test_vat_of_cart_after_discount(self):
        cart = ShoppingCart()
        cart.add("Mantel", 119.00)
        self.assertEqual(cart.vat(), 17.10)

    def test_item_count_counts_all_units(self):
        cart = ShoppingCart()
        cart.add("Buch", 12.50, 2)
        cart.add("Stift", 1.20, 3)
        self.assertEqual(cart.item_count(), 5)

    def test_clear_empties_cart(self):
        cart = ShoppingCart()
        cart.add("Buch", 12.50)
        cart.clear()
        self.assertTrue(cart.is_empty())

    def test_receipt_lists_items(self):
        cart = ShoppingCart()
        cart.add("Buch", 12.50, 2)
        self.assertEqual(cart.receipt_lines()[0], "Buch: 2 x 12,50 EUR")

    def test_receipt_total_is_amount_due(self):
        cart = ShoppingCart()
        cart.add("Jacke", 105.00)
        self.assertIn("Gesamt: 99,40 EUR", cart.receipt_lines())


if __name__ == "__main__":
    unittest.main()
