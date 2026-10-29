import unittest

from code_with_defects.bank_account import BankAccount


class TestCreateAccount(unittest.TestCase):
    def test_start_balance_zero_with_overdraft_is_allowed(self):
        account = BankAccount("Anna", balance=0.0, overdraft_limit=200.0)
        self.assertEqual(account.balance, 0.0)

    def test_start_balance_exactly_at_limit_is_allowed(self):
        account = BankAccount("Anna", balance=-200.0, overdraft_limit=200.0)
        self.assertEqual(account.balance, -200.0)

    def test_start_balance_below_limit_is_rejected(self):
        with self.assertRaises(ValueError):
            BankAccount("Anna", balance=-201.0, overdraft_limit=200.0)

    def test_negative_overdraft_limit_is_rejected(self):
        with self.assertRaises(ValueError):
            BankAccount("Anna", balance=100.0, overdraft_limit=-50.0)


class TestDeposit(unittest.TestCase):
    def test_deposit_increases_balance(self):
        account = BankAccount("Anna", balance=100.0)
        account.deposit(50.0)
        self.assertEqual(account.balance, 150.0)

    def test_deposit_zero_is_rejected(self):
        account = BankAccount("Anna", balance=100.0)
        with self.assertRaises(ValueError):
            account.deposit(0.0)
        self.assertEqual(account.balance, 100.0)

    def test_deposit_negative_is_rejected(self):
        account = BankAccount("Anna", balance=100.0)
        with self.assertRaises(ValueError):
            account.deposit(-20.0)
        self.assertEqual(account.balance, 100.0)


class TestWithdraw(unittest.TestCase):
    def test_withdraw_decreases_balance(self):
        account = BankAccount("Anna", balance=100.0)
        account.withdraw(30.0)
        self.assertEqual(account.balance, 70.0)

    def test_withdraw_into_overdraft_is_allowed(self):
        account = BankAccount("Anna", balance=150.0, overdraft_limit=200.0)
        account.withdraw(300.0)
        self.assertEqual(account.balance, -150.0)

    def test_withdraw_exactly_to_limit_is_allowed(self):
        account = BankAccount("Anna", balance=100.0, overdraft_limit=200.0)
        account.withdraw(300.0)
        self.assertEqual(account.balance, -200.0)

    def test_withdraw_beyond_limit_is_rejected_and_balance_unchanged(self):
        account = BankAccount("Anna", balance=-150.0, overdraft_limit=200.0)
        with self.assertRaises(ValueError):
            account.withdraw(100.0)
        self.assertEqual(account.balance, -150.0)

    def test_withdraw_without_overdraft_cannot_go_negative(self):
        account = BankAccount("Ben", balance=50.0)
        with self.assertRaises(ValueError):
            account.withdraw(50.01)
        self.assertEqual(account.balance, 50.0)

    def test_withdraw_zero_is_rejected(self):
        account = BankAccount("Anna", balance=100.0)
        with self.assertRaises(ValueError):
            account.withdraw(0.0)
        self.assertEqual(account.balance, 100.0)


class TestTransfer(unittest.TestCase):
    def test_transfer_moves_money(self):
        ben = BankAccount("Ben", balance=50.0)
        anna = BankAccount("Anna", balance=-150.0, overdraft_limit=200.0)
        ben.transfer(30.0, anna)
        self.assertEqual(ben.balance, 20.0)
        self.assertEqual(anna.balance, -120.0)

    def test_failed_transfer_changes_nothing(self):
        ben = BankAccount("Ben", balance=20.0)
        anna = BankAccount("Anna", balance=-120.0, overdraft_limit=200.0)
        with self.assertRaises(ValueError):
            ben.transfer(100.0, anna)
        self.assertEqual(ben.balance, 20.0)
        self.assertEqual(anna.balance, -120.0)

    def test_transfer_to_own_account_is_rejected(self):
        anna = BankAccount("Anna", balance=100.0)
        with self.assertRaises(ValueError):
            anna.transfer(10.0, anna)
        self.assertEqual(anna.balance, 100.0)


class TestInterest(unittest.TestCase):
    def test_positive_balance_gets_savings_interest(self):
        account = BankAccount("Ben", balance=20.0)
        account.apply_interest(savings_rate=0.02, overdraft_rate=0.10)
        self.assertEqual(account.balance, 20.40)

    def test_negative_balance_pays_overdraft_interest(self):
        account = BankAccount("Anna", balance=-120.0, overdraft_limit=200.0)
        account.apply_interest(savings_rate=0.02, overdraft_rate=0.10)
        self.assertEqual(account.balance, -132.00)

    def test_zero_balance_gets_no_interest(self):
        account = BankAccount("Anna", balance=0.0)
        account.apply_interest(savings_rate=0.02, overdraft_rate=0.10)
        self.assertEqual(account.balance, 0.0)

    def test_interest_is_rounded_to_cents(self):
        account = BankAccount("Ben", balance=10.55)
        account.apply_interest(savings_rate=0.03, overdraft_rate=0.10)
        self.assertEqual(account.balance, 10.87)


if __name__ == "__main__":
    unittest.main()
