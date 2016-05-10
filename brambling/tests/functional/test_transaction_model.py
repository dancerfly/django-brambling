from decimal import Decimal

from django.test import TestCase

from brambling.models import Transaction
from brambling.tests.factories import (
    TransactionFactory,
)


class TransactionModelTestCase(TestCase):
    def test_get_refundable_amount(self):
        txn = TransactionFactory(amount=Decimal("2.00"))
        self.assertEqual(txn.get_refundable_amount(), Decimal("2.00"))

    def test_get_refundable_amount__refunded(self):
        txn = TransactionFactory(
            amount=Decimal("2.00"),
        )
        TransactionFactory(
            related_transaction=txn,
            transaction_type=Transaction.REFUND,
            amount=Decimal("-2.00"),
        )
        self.assertEqual(txn.get_refundable_amount(), Decimal("0.00"))

    def test_refund(self):
        txn = TransactionFactory(amount=Decimal("2.00"))
        self.assertEqual(txn.get_refundable_amount(), Decimal("2.00"))
        self.assertEqual(txn.related_transaction_set.count(), 0)
        refund = txn.refund()
        self.assertIsInstance(refund, Transaction)
        self.assertEqual(txn.get_refundable_amount(), Decimal("0.00"))
        self.assertEqual(txn.related_transaction_set.count(), 1)

    def test_refund__refunded(self):
        txn = TransactionFactory(amount=Decimal("2.00"))
        self.assertEqual(txn.get_refundable_amount(), Decimal("2.00"))
        self.assertEqual(txn.related_transaction_set.count(), 0)
        refund = txn.refund()
        self.assertIsInstance(refund, Transaction)
        self.assertEqual(txn.get_refundable_amount(), Decimal("0.00"))
        self.assertEqual(txn.related_transaction_set.count(), 1)

        refund = txn.refund()
        self.assertIsNone(refund)
        self.assertEqual(txn.get_refundable_amount(), Decimal("0.00"))
        self.assertEqual(txn.related_transaction_set.count(), 1)

    def test_refund__zero_amount(self):
        txn = TransactionFactory(amount=Decimal("0"))
        self.assertEqual(txn.get_refundable_amount(), Decimal("0.00"))
        self.assertEqual(txn.related_transaction_set.count(), 0)
        refund = txn.refund()
        self.assertIsInstance(refund, Transaction)
        self.assertEqual(txn.get_refundable_amount(), Decimal("0.00"))
        self.assertEqual(txn.related_transaction_set.count(), 1)

    def test_refund__zero_amount__refunded(self):
        txn = TransactionFactory(amount=Decimal("0"))
        self.assertEqual(txn.get_refundable_amount(), Decimal("0.00"))
        self.assertEqual(txn.related_transaction_set.count(), 0)
        refund = txn.refund()
        self.assertIsInstance(refund, Transaction)
        self.assertEqual(txn.get_refundable_amount(), Decimal("0.00"))
        self.assertEqual(txn.related_transaction_set.count(), 1)

        refund = txn.refund()
        self.assertIsNone(refund)
        self.assertEqual(txn.get_refundable_amount(), Decimal("0.00"))
        self.assertEqual(txn.related_transaction_set.count(), 1)

    def test_unconfirmed_check(self):
        t = Transaction(is_confirmed=False, method=Transaction.CHECK)
        self.assertTrue(t.is_unconfirmed_check())

    def test_confirmed_check(self):
        t = Transaction(is_confirmed=True, method=Transaction.CHECK)
        self.assertFalse(t.is_unconfirmed_check())

    def test_confirmed_noncheck(self):
        t = Transaction(is_confirmed=True, method=Transaction.OTHER)
        self.assertFalse(t.is_unconfirmed_check())

    def test_unconfirmed_noncheck(self):
        t = Transaction(is_confirmed=False, method=Transaction.OTHER)
        self.assertFalse(t.is_unconfirmed_check())
