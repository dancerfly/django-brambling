from django.test import TestCase

from brambling.forms.organizer import ManualPaymentForm
from brambling.models import Transaction
from brambling.tests.factories import OrderFactory, PersonFactory, CardFactory


class ManualPaymentFormTestCase(TestCase):
    def test_creation(self):
        order = OrderFactory()
        user = PersonFactory()
        form = ManualPaymentForm(order=order, user=user, data={'amount': 10, 'method': Transaction.FAKE})
        self.assertFalse(form.errors)
        self.assertTrue(form.is_bound)
        txn = form.save()
        self.assertEqual(txn.amount, 10)
        self.assertEqual(txn.order, order)
        self.assertEqual(txn.event, order.event)
        self.assertEqual(txn.transaction_type, Transaction.PURCHASE)
        self.assertEqual(txn.method, Transaction.FAKE)
        self.assertEqual(txn.created_by, user)
        self.assertEqual(txn.is_confirmed, True)
        self.assertEqual(txn.api_type, order.event.api_type)
