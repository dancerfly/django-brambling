import mock

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


class TransactionRefundTestCase(TestCase):
    def setUp(self):
        self.person = PersonFactory()
        self.event = EventFactory()
        self.item = ItemFactory(event=self.event, name='Multipass')
        self.order = OrderFactory(event=self.event, person=self.person)
        self.item_option1 = ItemOptionFactory(price=100, item=self.item, name='Gold')
        self.item_option2 = ItemOptionFactory(price=100, item=self.item, name='Gold')
        self.bought_item1 = BoughtItem.objects.create(item_option=self.item_option1, order=self.order, price=Decimal(0), status=BoughtItem.BOUGHT)
        self.bought_item2 = BoughtItem.objects.create(item_option=self.item_option2, order=self.order, price=Decimal(0), status=BoughtItem.BOUGHT)
        self.txn = TransactionFactory(amount=Decimal("20"), order=self.order)
        self.txn.bought_items.add(self.bought_item1, self.bought_item2)

    def test_refund_no_args(self):
        self.txn.amount = Decimal("2.00")
        self.txn.save()
        self.assertEqual(self.txn.get_refundable_amount(), Decimal("2.00"))
        self.assertEqual(self.txn.related_transaction_set.count(), 0)
        refund = self.txn.refund()
        self.assertIsInstance(refund, Transaction)
        self.assertEqual(self.txn.get_refundable_amount(), Decimal("0.00"))
        self.assertEqual(self.txn.related_transaction_set.count(), 1)

    def test_refund_no_args__refunded(self):
        self.txn.amount = Decimal("2.00")
        self.txn.save()
        self.assertEqual(self.txn.get_refundable_amount(), Decimal("2.00"))
        self.assertEqual(self.txn.related_transaction_set.count(), 0)
        refund = self.txn.refund()
        self.assertIsInstance(refund, Transaction)
        self.assertEqual(self.txn.get_refundable_amount(), Decimal("0.00"))
        self.assertEqual(self.txn.related_transaction_set.count(), 1)

        refund = self.txn.refund()
        self.assertIsNone(refund)
        self.assertEqual(self.txn.get_refundable_amount(), Decimal("0.00"))
        self.assertEqual(self.txn.related_transaction_set.count(), 1)

    def test_refund__zero_amount_with_item(self):
        self.txn.amount = Decimal("0")
        self.txn.save()
        self.assertEqual(self.txn.get_refundable_amount(), Decimal("0"))
        self.assertQuerysetEqual(self.txn.get_returnable_items(), [repr(self.bought_item1), repr(self.bought_item2)])

        refund = self.txn.refund()
        self.assertIsInstance(refund, Transaction)
        self.assertEqual(self.txn.get_refundable_amount(), Decimal("0.00"))
        self.assertEqual(len(self.txn.get_returnable_items()), 0)

    def test_refund_partial_amount(self):
        self.txn.amount = Decimal("20.00")
        self.txn.save()
        refund = self.txn.refund(amount=Decimal(10))
        self.assertEqual(refund.amount, Decimal(-10))
        self.assertEqual(self.txn.get_refundable_amount(), Decimal(10))

    def test_refund_one_item(self):
        refund = self.txn.refund(bought_items=BoughtItem.objects.filter(pk=self.bought_item1.pk))
        self.bought_item1.refresh_from_db()
        self.assertEqual(refund.bought_items.get(), self.bought_item1)
        self.assertEqual(self.bought_item1.status, BoughtItem.REFUNDED)
        self.assertNotEqual(self.bought_item2, BoughtItem.BOUGHT)

    def test_nothing_refund(self):
        refund = self.txn.refund(bought_items=BoughtItem.objects.none(), amount=Decimal("0"))
        self.assertIsNone(refund)

    def test_excessive_refund_amount(self):
        self.txn.amount = Decimal("20.00")
        self.txn.save()
        with self.assertRaises(ValueError):
            self.txn.refund(amount=Decimal("2000.00"))

    def test_alien_item_return(self):
        alien_order = OrderFactory(event=self.event, person=self.person)
        alien_item = BoughtItem.objects.create(item_option=self.item_option1, price=Decimal(0), status=BoughtItem.BOUGHT, order=alien_order)
        with self.assertRaises(ValueError):
            self.txn.refund(bought_items=BoughtItem.objects.filter(pk=alien_item.pk))

    def test_negative_refund_error(self):
        with self.assertRaises(ValueError):
            self.txn.refund(amount=Decimal("-20.00"))

    @mock.patch('brambling.models.dwolla_refund')
    def test_dwolla_refund(self, dwolla_refund):
        dwolla_refund.return_value = {
            'fundsSource': 'Balance',
            'pin': 1234,
            'Amount': 20.00,
            'oauth_token': 'AN OAUTH TOKEN',
            'TransactionId': self.txn.remote_id
        }
        self.txn.method = Transaction.DWOLLA
        self.txn.amount = Decimal("20.00")
        self.txn.save()
        self.txn.refund(dwolla_pin="1234")
        dwolla_refund.assert_called_once_with(order=self.txn.order,
                                              event=self.txn.order.event,
                                              payment_id=self.txn.remote_id,
                                              amount=Decimal("20.00"),
                                              pin="1234")

    @mock.patch('brambling.models.Transaction.from_stripe_refund')
    @mock.patch('brambling.models.stripe_refund')
    def test_stripe_refund(self, stripe_refund, from_stripe_refund):
        self.txn.method = Transaction.STRIPE
        self.txn.amount = Decimal("20.00")
        self.txn.save()
        self.txn.refund()
        stripe_refund.assert_called_once_with(order=self.txn.order,
                                              event=self.txn.order.event,
                                              payment_id=self.txn.remote_id,
                                              amount=Decimal("20.00"))
