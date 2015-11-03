from decimal import Decimal

from django.test import TestCase

from brambling.models import Transaction
from brambling.tests.factories import (
    TransactionFactory,
)


class TransactionModelTestCase(TestCase):
    def test_can_refund(self):
        txn = TransactionFactory(amount=Decimal("2.00"))
        self.assertTrue(txn.can_refund())

    def test_can_refund__refunded(self):
        txn = TransactionFactory(
            amount=Decimal("2.00"),
        )
        txn2 = TransactionFactory(
            related_transaction=txn,
            transaction_type=Transaction.REFUND,
            amount=Decimal("-2.00"),
        )
        self.assertFalse(txn.can_refund())

    def test_can_refund__zero_amount(self):
        txn = TransactionFactory(
            amount=Decimal("0"),
        )
        self.assertTrue(txn.can_refund())

    def test_refund(self):
        txn = TransactionFactory(amount=Decimal("2.00"))
        self.assertTrue(txn.can_refund())
        self.assertEqual(txn.related_transaction_set.count(), 0)
        refund = txn.refund()
        self.assertIsInstance(refund, Transaction)
        self.assertFalse(txn.can_refund())
        self.assertEqual(txn.related_transaction_set.count(), 1)

    def test_refund__refunded(self):
        txn = TransactionFactory(amount=Decimal("2.00"))
        self.assertTrue(txn.can_refund())
        self.assertEqual(txn.related_transaction_set.count(), 0)
        refund = txn.refund()
        self.assertIsInstance(refund, Transaction)
        self.assertFalse(txn.can_refund())
        self.assertEqual(txn.related_transaction_set.count(), 1)

        refund = txn.refund()
        self.assertIsNone(refund)
        self.assertFalse(txn.can_refund())
        self.assertEqual(txn.related_transaction_set.count(), 1)

    def test_refund__zero_amount(self):
        txn = TransactionFactory(amount=Decimal("0"))
        self.assertTrue(txn.can_refund())
        self.assertEqual(txn.related_transaction_set.count(), 0)
        refund = txn.refund()
        self.assertIsInstance(refund, Transaction)
        self.assertFalse(txn.can_refund())
        self.assertEqual(txn.related_transaction_set.count(), 1)

    def test_refund__zero_amount__refunded(self):
        txn = TransactionFactory(amount=Decimal("0"))
        self.assertTrue(txn.can_refund())
        self.assertEqual(txn.related_transaction_set.count(), 0)
        refund = txn.refund()
        self.assertIsInstance(refund, Transaction)
        self.assertFalse(txn.can_refund())
        self.assertEqual(txn.related_transaction_set.count(), 1)

        refund = txn.refund()
        self.assertIsNone(refund)
        self.assertFalse(txn.can_refund())
        self.assertEqual(txn.related_transaction_set.count(), 1)
