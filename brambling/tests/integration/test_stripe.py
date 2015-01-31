from decimal import Decimal

from django.test import TestCase
import stripe

from brambling.models import Event, Transaction
from brambling.tests.factories import EventFactory
from brambling.utils.payment import (stripe_prep, stripe_charge,
                                     stripe_is_connected)


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
