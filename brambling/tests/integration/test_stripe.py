from decimal import Decimal

from django.test import TestCase
import stripe

from brambling.models import Event, Transaction
from brambling.tests.factories import EventFactory
from brambling.utils.payment import (stripe_prep, stripe_charge,
                                     stripe_is_connected, stripe_refund)


class StripeTestCase(TestCase):
    def test_charge__no_customer(self):
        event = EventFactory(api_type=Event.TEST,
                             application_fee_percent=2.5)
        self.assertTrue(stripe_is_connected(event, Event.TEST))
        stripe_prep(Event.TEST)

        token = stripe.Token.create(
            card={
                "number": '4242424242424242',
                "exp_month": 12,
                "exp_year": 2050,
                "cvc": '123'
            },
        )
        charge = stripe_charge(token, 42.15, event)
        self.assertIsInstance(charge.balance_transaction, stripe.StripeObject)
        self.assertEqual(charge.balance_transaction.object, "balance_transaction")
        self.assertEqual(len(charge.balance_transaction.fee_details), 2)

        txn = Transaction.from_stripe_charge(charge, api_type=event.api_type)
        # 42.15 * 0.025 = 1.05
        self.assertEqual(txn.application_fee, Decimal('1.05'))
        # (42.15 * 0.029) + 0.30 = 1.52
        self.assertEqual(txn.processing_fee, Decimal('1.52'))

        refund = stripe_refund(event, txn.remote_id, txn.amount)

        refund_txn = Transaction.from_stripe_refund(refund, api_type=event.api_type, related_transaction=txn)
        self.assertEqual(refund_txn.amount, -1 * txn.amount)
        self.assertEqual(refund_txn.application_fee, -1 * txn.application_fee)
        self.assertEqual(refund_txn.processing_fee, -1 * txn.processing_fee)

    def test_charge__customer(self):
        event = EventFactory(api_type=Event.TEST,
                             application_fee_percent=2.5)
        self.assertTrue(stripe_is_connected(event, Event.TEST))
        stripe_prep(Event.TEST)

        token = stripe.Token.create(
            card={
                "number": '4242424242424242',
                "exp_month": 12,
                "exp_year": 2050,
                "cvc": '123'
            },
        )
        customer = stripe.Customer.create(
            card=token,
        )
        card = customer.default_card
        charge = stripe_charge(card, 42.15, event, customer)
        self.assertIsInstance(charge.balance_transaction, stripe.StripeObject)
        self.assertEqual(charge.balance_transaction.object, "balance_transaction")
        self.assertEqual(len(charge.balance_transaction.fee_details), 2)

        txn = Transaction.from_stripe_charge(charge, api_type=event.api_type)
        # 42.15 * 0.025 = 1.05
        self.assertEqual(txn.application_fee, Decimal('1.05'))
        # (42.15 * 0.029) + 0.30 = 1.52
        self.assertEqual(txn.processing_fee, Decimal('1.52'))

        refund = stripe_refund(event, txn.remote_id, txn.amount)

        refund_txn = Transaction.from_stripe_refund(refund, api_type=event.api_type, related_transaction=txn)
        self.assertEqual(refund_txn.amount, -1 * txn.amount)
        self.assertEqual(refund_txn.application_fee, -1 * txn.application_fee)
        self.assertEqual(refund_txn.processing_fee, -1 * txn.processing_fee)
