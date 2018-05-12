from decimal import Decimal
from unittest import skipUnless
import os

from django.test import TestCase
import stripe

from brambling.models import Transaction
from brambling.payment.core import (
    InvalidAmountException,
    TEST,
)
from brambling.payment.stripe.api import (
    stripe_get_customer,
    stripe_add_card,
    stripe_charge,
    stripe_delete_card,
    stripe_refund,
)
from brambling.payment.stripe.core import stripe_prep
from brambling.tests.factories import (
    EventFactory,
    OrderFactory,
    PersonFactory,
)


@skipUnless(os.environ.get('STRIPE_TEST_APPLICATION_ID'), 'stripe test settings required')
class StripeChargeTestCase(TestCase):
    def test_charge__negative_amount(self):
        event = EventFactory(api_type=TEST,
                             application_fee_percent=Decimal('2.5'))
        order = OrderFactory(event=event)
        stripe_prep(TEST)
        stripe.api_key = event.organization.stripe_test_access_token
        token = stripe.Token.create(
            card={
                "number": '4242424242424242',
                "exp_month": 12,
                "exp_year": 2050,
                "cvc": '123'
            },
        )

        with self.assertRaises(InvalidAmountException):
            stripe_charge(token, amount=Decimal('-9.01'), order=order,
                          event=event)

    def test_charge__no_customer(self):
        event = EventFactory(api_type=TEST,
                             application_fee_percent=Decimal('2.5'))
        order = OrderFactory(event=event)
        self.assertTrue(event.stripe_connected())
        stripe_prep(TEST)
        stripe.api_key = event.organization.stripe_test_access_token

        token = stripe.Token.create(
            card={
                "number": '4242424242424242',
                "exp_month": 12,
                "exp_year": 2050,
                "cvc": '123'
            },
        )
        charge = stripe_charge(
            token,
            amount=42.15,
            order=order,
            event=event,
        )
        self.assertIsInstance(charge.balance_transaction, stripe.StripeObject)
        self.assertEqual(charge.balance_transaction.object, "balance_transaction")
        self.assertEqual(len(charge.balance_transaction.fee_details), 2)
        self.assertEqual(charge.metadata, {'order': order.code, 'event': event.name})

        txn = Transaction.from_stripe_charge(charge, api_type=event.api_type, event=event)
        # 42.15 * 0.025 = 1.05
        self.assertEqual(txn.application_fee, Decimal('1.05'))
        # (42.15 * 0.029) + 0.30 = 1.52
        self.assertEqual(txn.processing_fee, Decimal('1.52'))

        refund = stripe_refund(
            order=order,
            event=event,
            payment_id=txn.remote_id,
            amount=txn.amount
        )
        self.assertEqual(refund['refund'].metadata, {'order': order.code, 'event': event.name})

        refund_txn = Transaction.from_stripe_refund(refund, api_type=event.api_type, related_transaction=txn, event=event)
        self.assertEqual(refund_txn.amount, -1 * txn.amount)
        self.assertEqual(refund_txn.application_fee, -1 * txn.application_fee)
        self.assertEqual(refund_txn.processing_fee, -1 * txn.processing_fee)

    def test_charge__customer(self):
        event = EventFactory(api_type=TEST,
                             application_fee_percent=Decimal('2.5'))
        order = OrderFactory(event=event)
        self.assertTrue(event.stripe_connected())
        stripe_prep(TEST)

        token = stripe.Token.create(
            card={
                "number": '4242424242424242',
                "exp_month": 12,
                "exp_year": 2050,
                "cvc": '123'
            },
        )
        customer = stripe.Customer.create(
            source=token,
        )
        source = customer.default_source
        charge = stripe_charge(
            source,
            amount=42.15,
            event=event,
            order=order,
            customer=customer
        )
        self.assertIsInstance(charge.balance_transaction, stripe.StripeObject)
        self.assertEqual(charge.balance_transaction.object, "balance_transaction")
        self.assertEqual(len(charge.balance_transaction.fee_details), 2)
        self.assertEqual(charge.metadata, {'order': order.code, 'event': event.name})

        txn = Transaction.from_stripe_charge(charge, api_type=event.api_type, event=event)
        # 42.15 * 0.025 = 1.05
        self.assertEqual(txn.application_fee, Decimal('1.05'))
        # (42.15 * 0.029) + 0.30 = 1.52
        self.assertEqual(txn.processing_fee, Decimal('1.52'))

        refund = stripe_refund(
            order=order,
            event=event,
            payment_id=txn.remote_id,
            amount=txn.amount
        )
        self.assertEqual(refund['refund'].metadata, {'order': order.code, 'event': event.name})

        refund_txn = Transaction.from_stripe_refund(refund, api_type=event.api_type, related_transaction=txn, event=event)
        self.assertEqual(refund_txn.amount, -1 * txn.amount)
        self.assertEqual(refund_txn.application_fee, -1 * txn.application_fee)
        self.assertEqual(refund_txn.processing_fee, -1 * txn.processing_fee)

    def test_partial_refunds(self):
        event = EventFactory(api_type=TEST,
                             application_fee_percent=Decimal('2.5'))
        order = OrderFactory(event=event)
        self.assertTrue(event.stripe_connected())
        stripe_prep(TEST)
        stripe.api_key = event.organization.stripe_test_access_token

        token = stripe.Token.create(
            card={
                "number": '4242424242424242',
                "exp_month": 12,
                "exp_year": 2050,
                "cvc": '123'
            },
        )
        charge = stripe_charge(
            token,
            amount=42.15,
            order=order,
            event=event,
        )
        self.assertIsInstance(charge.balance_transaction, stripe.StripeObject)
        self.assertEqual(charge.balance_transaction.object, "balance_transaction")
        self.assertEqual(len(charge.balance_transaction.fee_details), 2)
        self.assertEqual(charge.metadata, {'order': order.code, 'event': event.name})

        txn = Transaction.from_stripe_charge(charge, api_type=event.api_type, event=event)
        # 42.15 * 0.025 = 1.05
        self.assertEqual(txn.application_fee, Decimal('1.05'))
        # (42.15 * 0.029) + 0.30 = 1.52
        self.assertEqual(txn.processing_fee, Decimal('1.52'))

        refund1_amount = 10
        refund1 = stripe_refund(
            order=order,
            event=event,
            payment_id=txn.remote_id,
            amount=refund1_amount
        )
        self.assertEqual(refund1['refund'].metadata, {'order': order.code, 'event': event.name})

        refund1_txn = Transaction.from_stripe_refund(refund1, api_type=event.api_type, related_transaction=txn, event=event)

        self.assertEqual(refund1_txn.amount, Decimal('-10.00'))
        # 10.00 * 0.025 = 0.25
        self.assertEqual(refund1_txn.application_fee, Decimal('-0.25'))
        # 10.00 * 0.029 = 0.29
        self.assertEqual(refund1_txn.processing_fee, Decimal('-0.29'))

        refund2_amount = 20
        refund2 = stripe_refund(
            order=order,
            event=event,
            payment_id=txn.remote_id,
            amount=refund2_amount
        )
        self.assertEqual(refund2['refund'].metadata, {'order': order.code, 'event': event.name})

        refund2_txn = Transaction.from_stripe_refund(refund2, api_type=event.api_type, related_transaction=txn, event=event)

        self.assertEqual(refund2_txn.amount, Decimal('-20.00'))
        # 20.00 * 0.025 = 0.50
        self.assertEqual(refund2_txn.application_fee, Decimal('-0.50'))
        # 20.00 * 0.029 = 0.58
        self.assertEqual(refund2_txn.processing_fee, Decimal('-0.58'))


class StripeCustomerTestCase(TestCase):
    @skipUnless(os.environ.get('STRIPE_TEST_APPLICATION_ID'), 'stripe test settings required')
    def test_get_customer(self):
        user = PersonFactory()
        self.assertEqual(user.stripe_test_customer_id, '')
        customer = stripe_get_customer(user, TEST)
        user.refresh_from_db()
        self.assertEqual(user.stripe_test_customer_id, customer.id)
        self.assertEqual(customer.email, user.email)

        new_customer = stripe_get_customer(user, TEST)
        self.assertEqual(new_customer.id, customer.id)
        user.refresh_from_db()
        self.assertEqual(user.stripe_test_customer_id, customer.id)

    def test_get_customer__no_create(self):
        user = PersonFactory()
        self.assertEqual(user.stripe_test_customer_id, '')
        customer = stripe_get_customer(user, TEST, create=False)
        self.assertIsNone(customer)
        user.refresh_from_db()
        self.assertEqual(user.stripe_test_customer_id, '')

    @skipUnless(os.environ.get('STRIPE_TEST_APPLICATION_ID'), 'stripe test settings required')
    def test_add_card(self):
        stripe_prep(TEST)
        token = stripe.Token.create(
            card={
                "number": '4242424242424242',
                "exp_month": 12,
                "exp_year": 2050,
                "cvc": '123'
            },
        )
        customer = stripe.Customer.create()
        self.assertEqual(customer.sources.total_count, 0)
        card = stripe_add_card(customer, token, TEST)
        customer = stripe.Customer.retrieve(customer.id)
        self.assertEqual(customer.sources.total_count, 1)
        stripe_delete_card(customer, card.id)
        customer = stripe.Customer.retrieve(customer.id)
        self.assertEqual(customer.sources.total_count, 0)
