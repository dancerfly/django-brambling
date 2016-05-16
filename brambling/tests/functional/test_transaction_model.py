from decimal import Decimal

from django.test import TestCase

from brambling.models import Transaction, BoughtItem
from brambling.tests.factories import (
    TransactionFactory, ItemFactory, ItemOptionFactory, EventFactory,
    PersonFactory, OrderFactory
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

    def test_refund__zero_amount_with_item(self):
        person = PersonFactory()
        event = EventFactory()
        item = ItemFactory(event=event, name='Multipass')
        order = OrderFactory(event=event, person=person)
        item_option = ItemOptionFactory(price=100, item=item, name='Gold')
        bought_item = BoughtItem.objects.create(item_option=item_option, order=order, price=Decimal(0), status=BoughtItem.BOUGHT)
        txn = TransactionFactory(amount=Decimal("0"))
        txn.bought_items.add(bought_item)

        self.assertEqual(txn.get_refundable_amount(), Decimal("0"))
        self.assertEqual(txn.get_returnable_items().get(), bought_item)

        refund = txn.refund()
        self.assertIsInstance(refund, Transaction)
        self.assertEqual(txn.get_refundable_amount(), Decimal("0.00"))
        self.assertEqual(len(txn.get_returnable_items()), 0)

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
