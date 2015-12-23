from decimal import Decimal
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from mock import patch
import stripe

from brambling.forms.orders import (OneTimePaymentForm,
                                    SavedCardPaymentForm,
                                    DwollaPaymentForm,
                                    CheckPaymentForm)
from brambling.models import Transaction
from brambling.tests.factories import OrderFactory, PersonFactory, CardFactory, DwollaUserAccountFactory, DwollaOrganizationAccountFactory


STRIPE_CHARGE = stripe.Charge.construct_from({
    "amount": 4215,
    "amount_refunded": 0,
    "balance_transaction": {
        "amount": 4215,
        "available_on": 1423872000,
        "created": 1423348868,
        "currency": "usd",
        "description": None,
        "fee": 257,
        "fee_details": [
            {
                "amount": 152,
                "application": None,
                "currency": "usd",
                "description": "Stripe processing fees",
                "type": "stripe_fee"
            },
            {
                "amount": 105,
                "application": "FAKE",
                "currency": "usd",
                "description": "Dancerfly application fee",
                "type": "application_fee"
            }
        ],
        "id": "FAKE",
        "net": 3958,
        "object": "balance_transaction",
        "source": "FAKE",
        "status": "pending",
        "type": "charge"
    },
    "captured": True,
    "card": {
        "address_city": None,
        "address_country": None,
        "address_line1": None,
        "address_line1_check": None,
        "address_line2": None,
        "address_state": None,
        "address_zip": None,
        "address_zip_check": None,
        "brand": "Visa",
        "country": "US",
        "customer": None,
        "cvc_check": "pass",
        "dynamic_last4": None,
        "exp_month": 12,
        "exp_year": 2050,
        "fingerprint": "FAKE",
        "funding": "credit",
        "id": "FAKE",
        "last4": "4242",
        "name": None,
        "object": "card"
    },
    "created": 1423348868,
    "currency": "usd",
    "customer": None,
    "description": None,
    "dispute": None,
    "failure_code": None,
    "failure_message": None,
    "fraud_details": {},
    "id": "FAKE",
    "invoice": None,
    "livemode": False,
    "metadata": {},
    "object": "charge",
    "paid": True,
    "receipt_email": None,
    "receipt_number": None,
    "refunded": False,
    "refunds": {
        "data": [],
        "has_more": False,
        "object": "list",
        "total_count": 0,
        "url": "/v1/charges/FAKE/refunds"
    },
    "shipping": None,
    "statement_descriptor": None
}, 'FAKE')


DWOLLA_CHARGE = {
    u'Amount': 42.15,
    u'ClearingDate': u'',
    u'Date': u'2015-01-31T02:41:38Z',
    u'Destination': {u'Id': u'FAKE_DEST',
                     u'Image': u'http://uat.dwolla.com/avatars/FAKE_DEST',
                     u'Name': u'Blah blah blah',
                     u'Type': u'Dwolla'},
    u'DestinationId': u'FAKE_DEST',
    u'DestinationName': u'Blah blah blah',
    u'Fees': [{u'Amount': 0.25, u'Id': 827529, u'Type': u'Dwolla Fee'},
              {u'Amount': 1.05, u'Id': 827530, u'Type': u'Facilitator Fee'}],
    u'Id': 827527,
    u'Metadata': None,
    u'Notes': u'',
    u'OriginalTransactionId': None,
    u'Source': {u'Id': u'FAKE_SOURCE',
                u'Image': u'http://uat.dwolla.com/avatars/FAKE_SOURCE',
                u'Name': u'John Doe',
                u'Type': u'Dwolla'},
    u'SourceId': u'FAKE_SOURCE',
    u'SourceName': u'John Doe',
    u'Status': u'processed',
    u'Type': u'money_received',
    u'UserType': u'Dwolla'
}

DWOLLA_SOURCES = [
    {
        "Id": "Balance",
        "Name": "My Dwolla Balance",
        "Type": "",
        "Verified": "true",
        "ProcessingType": ""
    },
]


class PaymentFormTestCase(TestCase):
    @patch('brambling.forms.orders.stripe_charge')
    @patch('brambling.forms.orders.stripe_prep')
    def test_one_time_payment_form(self, stripe_prep, stripe_charge):
        stripe_charge.return_value = STRIPE_CHARGE
        order = OrderFactory()
        event = order.event
        person = PersonFactory()
        token = 'FAKE_TOKEN'
        form = OneTimePaymentForm(order=order, amount=Decimal('42.15'), data={'token': token}, user=person)
        self.assertTrue(form.is_bound)
        self.assertFalse(form.errors)
        stripe_charge.assert_called_once_with(
            token,
            amount=Decimal('42.15'),
            event=event,
            order=order,
        )
        self.assertEqual(stripe_prep.call_count, 0)
        txn = form.save()
        self.assertIsInstance(txn, Transaction)
        self.assertEqual(txn.event, event)
        self.assertEqual(txn.amount, Decimal('42.15'))
        self.assertEqual(txn.application_fee, Decimal('1.05'))
        self.assertEqual(txn.processing_fee, Decimal('1.52'))

    @patch('brambling.forms.orders.stripe_charge')
    @patch('brambling.forms.orders.stripe_prep')
    def test_saved_card_payment_form(self, stripe_prep, stripe_charge):
        stripe_charge.return_value = STRIPE_CHARGE
        person = PersonFactory(stripe_test_customer_id='FAKE_CUSTOMER_ID')
        order = OrderFactory(person=person)
        event = order.event
        card = CardFactory(is_saved=True)
        person.cards.add(card)
        person.save()
        form = SavedCardPaymentForm(order, Decimal('42.15'), data={'card': card.pk})
        self.assertTrue(form.is_bound)
        self.assertFalse(form.errors)
        stripe_charge.assert_called_once_with(
            card.stripe_card_id,
            amount=Decimal('42.15'),
            event=event,
            order=order,
            customer='FAKE_CUSTOMER_ID'
        )
        self.assertEqual(stripe_prep.call_count, 0)
        txn = form.save()
        self.assertIsInstance(txn, Transaction)
        self.assertEqual(txn.event, event)
        self.assertEqual(txn.amount, Decimal('42.15'))
        self.assertEqual(txn.application_fee, Decimal('1.05'))
        self.assertEqual(txn.processing_fee, Decimal('1.52'))

    @patch('brambling.forms.orders.dwolla_get_sources')
    @patch('brambling.forms.orders.dwolla_charge')
    def test_dwolla_payment_form(self, dwolla_charge, dwolla_get_sources):
        dwolla_charge.return_value = DWOLLA_CHARGE
        dwolla_get_sources.return_value = DWOLLA_SOURCES
        order = OrderFactory()
        event = order.event
        event.organization.dwolla_test_account = DwollaOrganizationAccountFactory()
        event.organization.save()
        person = PersonFactory()
        person.dwolla_test_account = DwollaUserAccountFactory()
        person.save()
        pin = '1234'
        source = 'Balance'
        form = DwollaPaymentForm(order=order, amount=Decimal('42.15'), data={'dwolla_pin': pin, 'source': source}, user=person)
        self.assertTrue(form.is_bound)
        self.assertFalse(form.errors)
        dwolla_charge.assert_called_once_with(
            account=person.dwolla_test_account,
            amount=42.15,
            event=event,
            pin=pin,
            source=source,
            order=order,
        )
        txn = form.save()
        self.assertIsInstance(txn, Transaction)
        self.assertEqual(txn.event, event)
        self.assertEqual(Decimal(str(txn.amount)), Decimal('42.15'))
        self.assertEqual(Decimal(str(txn.application_fee)), Decimal('1.05'))
        self.assertEqual(Decimal(str(txn.processing_fee)), Decimal('0.25'))

    @patch('brambling.forms.orders.dwolla_get_sources')
    @patch('dwolla.oauth.refresh')
    def test_dwolla_payment_form_handles_valueerror(self, oauth_refresh, dwolla_get_sources):
        oauth_refresh.return_value = {
            'error': 'access_denied',
            'error_description': 'Arbitrary error code.'
        }
        dwolla_get_sources.return_value = DWOLLA_SOURCES
        order = OrderFactory()
        order.event.organization.dwolla_test_account = DwollaOrganizationAccountFactory(
            access_token_expires=timezone.now() - timedelta(1)
        )
        order.event.organization.save()
        person = PersonFactory()
        person.dwolla_test_account = DwollaUserAccountFactory()
        person.save()
        pin = '1234'
        source = 'Balance'
        form = DwollaPaymentForm(order=order, amount=Decimal('42.15'), data={'dwolla_pin': pin, 'source': source}, user=person)
        self.assertTrue(form.is_bound)
        self.assertTrue(form.errors)
        self.assertEqual(form.errors['__all__'], [oauth_refresh.return_value['error_description']])

    def test_check_payment_form(self):
        order = OrderFactory()
        event = order.event
        form = CheckPaymentForm(order=order, amount=Decimal('42.15'), data={})
        self.assertTrue(form.is_bound)
        self.assertFalse(form.errors)
        txn = form.save()
        self.assertIsInstance(txn, Transaction)
        self.assertEqual(txn.event, event)
        self.assertEqual(txn.amount, Decimal('42.15'))
        self.assertEqual(txn.application_fee, Decimal('0'))
        self.assertEqual(txn.processing_fee, Decimal('0'))
