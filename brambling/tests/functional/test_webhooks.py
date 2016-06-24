import json
import os

import copy
from django.core.exceptions import SuspiciousOperation
from django.core.urlresolvers import reverse
from django.http import Http404
from django.test import Client, TestCase, RequestFactory
import mock
import stripe
import vcr

from brambling.models import Transaction
from brambling.payment.stripe.core import stripe_prep
from brambling.payment.core import TEST
from brambling.tests.factories import (TransactionFactory, OrderFactory,
                                       EventFactory, ItemFactory,
                                       ItemOptionFactory)
from brambling.views.payment import DwollaWebhookView, StripeWebhookView, webhooks


VCR_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


TRANSACTION_STATUS_DATA = {
    "Id": "4444962",
    "Type": "Transaction",
    "Subtype": "Status",
    "Created": "2014-01-22T16:55:04Z",
    "Triggered": "2014-01-22T16:55:04Z",
    "Value": "processed",
    "Transaction": {
        "Type": "money_sent",
        "Notes": "",
        "Fees": [],
        "Id": 4444962,
        "Source": {
            "Id": "812-687-7049",
            "Name": "Gordon Zheng",
            "Type": "Dwolla"
        },
        "Destination": {
            "Id": "812-713-9234",
            "Name": "Reflector by Dwolla",
            "Type": "Dwolla"
        },
        "Amount": 0.01,
        "SentDate": "2014-01-22T16:55:04Z",
        "ClearingDate": "2014-01-22T16:55:04Z",
        "Status": "processed"
    },
    "Metadata": {
        "InvoiceDate": "12-06-2014",
        "Priority": "High",
        "TShirtSize": "Small",
        "blah": "blah"
    }

}


STRIPE_REFUND_EVENT = json.loads("""{
  "api_version": "2015-01-11",
  "created": 1464101467,
  "data": {
    "object": {
      "amount": 12000,
      "amount_refunded": 6000,
      "application_fee": null,
      "balance_transaction": "txn_18C9kF2dPuL5A6ooysxS4uFL",
      "captured": true,
      "card": {
        "address_city": null,
        "address_country": null,
        "address_line1": null,
        "address_line1_check": null,
        "address_line2": null,
        "address_state": null,
        "address_zip": null,
        "address_zip_check": null,
        "brand": "Visa",
        "country": "US",
        "customer": null,
        "cvc_check": "pass",
        "dynamic_last4": null,
        "exp_month": 11,
        "exp_year": 2019,
        "fingerprint": "l4ENmRZWbEtyXQRg",
        "funding": "credit",
        "id": "card_18C9kF2dPuL5A6ooIVeNe8kV",
        "last4": "4242",
        "metadata": {},
        "name": null,
        "object": "card",
        "tokenization_method": null
      },
      "created": 1463497467,
      "currency": "usd",
      "customer": null,
      "description": null,
      "destination": null,
      "dispute": null,
      "failure_code": null,
      "failure_message": null,
      "fraud_details": {},
      "id": "ch_18C9kF2dPuL5A6ooUE5opsBX",
      "invoice": null,
      "livemode": false,
      "metadata": {
        "event": "Demo Event",
        "order": "7pMR6czT"
      },
      "object": "charge",
      "order": null,
      "paid": true,
      "receipt_email": null,
      "receipt_number": null,
      "refunded": false,
      "refunds": {
        "data": [
          {
            "amount": 6000,
            "balance_transaction": "txn_18EgsB2dPuL5A6oozQ0nLPkz",
            "charge": "ch_18C9kF2dPuL5A6ooUE5opsBX",
            "created": 1464101467,
            "currency": "usd",
            "id": "re_18EgsB2dPuL5A6ooGEq33q9o",
            "metadata": {
              "event": "Demo Event",
              "order": "7pMR6czT"
            },
            "object": "refund",
            "reason": null,
            "receipt_number": null,
            "status": "succeeded"
          }
        ],
        "has_more": false,
        "object": "list",
        "total_count": 1,
        "url": "/v1/charges/ch_18C9kF2dPuL5A6ooUE5opsBX/refunds"
      },
      "shipping": null,
      "source": {
        "address_city": null,
        "address_country": null,
        "address_line1": null,
        "address_line1_check": null,
        "address_line2": null,
        "address_state": null,
        "address_zip": null,
        "address_zip_check": null,
        "brand": "Visa",
        "country": "US",
        "customer": null,
        "cvc_check": "pass",
        "dynamic_last4": null,
        "exp_month": 11,
        "exp_year": 2019,
        "fingerprint": "l4ENmRZWbEtyXQRg",
        "funding": "credit",
        "id": "card_18C9kF2dPuL5A6ooIVeNe8kV",
        "last4": "4242",
        "metadata": {},
        "name": null,
        "object": "card",
        "tokenization_method": null
      },
      "source_transfer": null,
      "statement_descriptor": null,
      "status": "paid"
    },
    "previous_attributes": {
      "amount_refunded": 0,
      "refunds": {
        "data": [],
        "has_more": false,
        "object": "list",
        "total_count": 0,
        "url": "/v1/charges/ch_18C9kF2dPuL5A6ooUE5opsBX/refunds"
      }
    }
  },
  "id": "evt_18EgsB2dPuL5A6oo1eOhCyit",
  "livemode": false,
  "object": "event",
  "pending_webhooks": 0,
  "request": "req_8ViIc76ys8DfCL",
  "type": "charge.refunded"
}""")


class DwollaWebhookTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = DwollaWebhookView.as_view()

    def test_should_not_check_csrf_tokens(self):
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post(reverse('brambling_dwolla_webhook'))
        self.assertNotEqual(response.status_code, 403)

    def test_bad_content_type(self):
        request = self.factory.post('/', content_type='text/xml', data='12345')
        with self.assertRaises(Http404) as cm:
            self.view(request)

        self.assertEqual(cm.exception.message, "Incorrect content type")

    def test_bad_json(self):
        request = self.factory.post('/', content_type='application/json', data='<html><head></head></html>')
        with self.assertRaises(Http404) as cm:
            self.view(request)

        self.assertEqual(cm.exception.message, "Webhook failed to decode request body")

    def test_unhandled_hook(self):
        data = {'Type': 'Transaction', 'Subtype': 'Returned'}
        request = self.factory.post(
            path='/',
            content_type='application/json',
            data=json.dumps(data)
        )
        with self.assertRaises(Http404) as cm:
            self.view(request)

        self.assertEqual(cm.exception.message, "Unhandled webhook type: Transaction / Returned")

    def test_missing_txn_id(self):
        data = {'Type': 'Transaction', 'Subtype': 'Status'}
        request = self.factory.post(
            path='/',
            content_type='application/json',
            data=json.dumps(data)
        )
        with self.assertRaises(Http404) as cm:
            self.view(request)

        self.assertEqual(cm.exception.message, "Data doesn't contain transaction id")

    def test_txn_does_not_exist(self):
        request = self.factory.post(
            path='/',
            content_type='application/json',
            data=json.dumps(TRANSACTION_STATUS_DATA)
        )
        with self.assertRaises(Http404) as cm:
            self.view(request)

        self.assertEqual(cm.exception.message, "Transaction doesn't exist")

    def test_bad_signature(self):
        txn = TransactionFactory(remote_id=TRANSACTION_STATUS_DATA['Id'], is_confirmed=False)
        dwolla_sig = 'abcde'
        data = json.dumps(TRANSACTION_STATUS_DATA)
        request = self.factory.post(
            path='/',
            content_type='application/json',
            data=data,
            HTTP_X_DWOLLA_SIGNATURE=dwolla_sig
        )
        with mock.patch.object(webhooks, 'verify', return_value=False) as verify:
            with self.assertRaises(SuspiciousOperation) as cm:
                self.view(request)

        self.assertEqual(cm.exception.message, "Transaction signature doesn't verify properly")
        verify.assert_called_once_with(dwolla_sig, data)

        txn = Transaction.objects.get(id=txn.id)
        self.assertFalse(txn.is_confirmed)

    def test_confirmation(self):
        txn = TransactionFactory(remote_id=TRANSACTION_STATUS_DATA['Id'], is_confirmed=False)
        dwolla_sig = 'abcde'
        data = json.dumps(TRANSACTION_STATUS_DATA)
        request = self.factory.post(
            path='/',
            content_type='application/json',
            data=data,
            HTTP_X_DWOLLA_SIGNATURE=dwolla_sig
        )
        with mock.patch.object(webhooks, 'verify', return_value=True) as verify:
            self.view(request)

        verify.assert_called_once_with(dwolla_sig, data)

        txn = Transaction.objects.get(id=txn.id)
        self.assertTrue(txn.is_confirmed)


class StripeWebhookBadRequestTestCase(TestCase):
    def setUp(self):
        stripe_prep(TEST)
        self.factory = RequestFactory()
        self.view = StripeWebhookView.as_view()

    def test_bad_content_type(self):
        request = self.factory.post('/', content_type='text/xml', data='12345')
        with self.assertRaises(Http404):
            self.view(request)

    def test_bad_json(self):
        request = self.factory.post('/', content_type='application/json',
                                    data='<html></html>')
        with self.assertRaises(Http404):
            self.view(request)

    def test_non_refund_event_type(self):
        non_refund_event = copy.deepcopy(STRIPE_REFUND_EVENT)
        non_refund_event['type'] = 'coupon.created'
        non_refund_event['data']['object'] = {
            "id": "25OFF",
            "object": "coupon",
            "amount_off": None,
            "created": 1466196826,
            "currency": "usd",
            "duration": "repeating",
            "duration_in_months": 3,
            "livemode": False,
            "max_redemptions": None,
            "metadata": {
            },
            "percent_off": 25,
            "redeem_by": None,
            "times_redeemed": 0,
            "valid": True,
        }
        data = json.dumps(non_refund_event)

        request = self.factory.post('/', content_type='application/json', data=data)
        response = self.view(request)
        self.assertEqual(response.status_code, 200)

    def test_missing_event_id(self):
        event_without_id = dict(STRIPE_REFUND_EVENT)
        del event_without_id['id']
        data = json.dumps(event_without_id)

        request = self.factory.post('/', content_type='application/json', data=data)
        with self.assertRaises(Http404):
            self.view(request)


class StripeWebhookRefundTestCase(TestCase):

    def setUp(self):
        stripe_prep(TEST)

        self.event = EventFactory()
        self.order = OrderFactory()

        self.factory = RequestFactory()
        self.view = StripeWebhookView.as_view()
        self.data = json.dumps(STRIPE_REFUND_EVENT)

        self.request = self.factory.post(path='/',
                                         content_type='application/json',
                                         data=self.data)

    def test_should_not_check_csrf_tokens(self):
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post(reverse('brambling_stripe_webhook'))
        self.assertNotEqual(response.status_code, 403)

    @mock.patch('stripe.Event.retrieve')
    def test_stripe_event_not_found(self, stripe_retrieve):
        stripe_retrieve.side_effect = stripe.error.InvalidRequestError(
            'not found', 1)

        with self.assertRaises(Http404):
            self.view(self.request)

    @mock.patch('stripe.Refund.retrieve')
    @vcr.use_cassette(os.path.join(VCR_DIR, 'stripe_webhook_refund_not_found.yaml'))
    def test_stripe_refund_not_found(self, refund_retrieve):
        refund_retrieve.side_effect = stripe.error.InvalidRequestError(
            'not found', 1)

        with self.assertRaises(Http404):
            self.view(self.request)

    @mock.patch('stripe.ApplicationFee.all')
    @vcr.use_cassette(os.path.join(VCR_DIR, 'stripe_webhook_fee_not_found.yaml'))
    def test_stripe_application_fee_not_found(self, application_fee_retrieve):
        remote_id = STRIPE_REFUND_EVENT['data']['object']['id']
        self.txn = TransactionFactory(event=self.event, order=self.order,
                                      remote_id=remote_id)
        empty_data = stripe.resource.ListObject.construct_from(
            {'data': []}, TEST)
        application_fee_retrieve.return_value = empty_data

        with self.assertRaises(Http404):
            self.view(self.request)

    @mock.patch('stripe.Charge.retrieve')
    @vcr.use_cassette(os.path.join(VCR_DIR, 'stripe_webhook_charge_not_found.yaml'))
    def test_stripe_charge_not_found(self, charge_retrieve):
        remote_id = STRIPE_REFUND_EVENT['data']['object']['id']
        self.txn = TransactionFactory(event=self.event, order=self.order,
                                      remote_id=remote_id)
        charge_retrieve.side_effect = stripe.error.InvalidRequestError(
            'not found', 1)

        with self.assertRaises(Http404):
            self.view(self.request)

    @vcr.use_cassette(os.path.join(VCR_DIR, 'test_stripe_webhook_refund.yaml'))
    def test_transaction_not_found(self):
        response = self.view(self.request)
        self.assertEqual(response.status_code, 200)
        with self.assertRaises(Transaction.DoesNotExist):
            Transaction.objects.get(
                remote_id=STRIPE_REFUND_EVENT['data']['object']['id'])

    @mock.patch('stripe.Event.retrieve')
    @vcr.use_cassette(os.path.join(VCR_DIR, 'stripe_webhook_charge_id_not_found.yaml'))
    def test_charge_id_not_found(self, stripe_retrieve):
        event_without_charge_id = copy.deepcopy(STRIPE_REFUND_EVENT)
        del event_without_charge_id['data']['object']['id']

        stripe_retrieve.return_value = stripe.resource.Event.construct_from(
            event_without_charge_id, TEST)

        with self.assertRaises(Http404):
            self.view(self.request)


class SuccessfulRefundWebhookTestCase(TestCase):

    def setUp(self):
        stripe_prep(TEST)

        self.event = EventFactory()
        self.order = OrderFactory()

        self.factory = RequestFactory()
        self.view = StripeWebhookView.as_view()
        self.data = json.dumps(STRIPE_REFUND_EVENT)

        self.request = self.factory.post(path='/',
                                         content_type='application/json',
                                         data=self.data)

        item = ItemFactory(event=self.event)
        item_option = ItemOptionFactory(price=60, item=item)
        self.order.add_to_cart(item_option)
        remote_id = STRIPE_REFUND_EVENT['data']['object']['id']
        self.txn = TransactionFactory(event=self.event, order=self.order,
                                      remote_id=remote_id)
        self.order.mark_cart_paid(self.txn)

    @vcr.use_cassette(os.path.join(VCR_DIR, 'stripe_webhook_refund_success.yaml'))
    def test_transaction_refunded_successfully(self):
        response = self.view(self.request)

        Transaction.objects.get(related_transaction=self.txn,
                                transaction_type=Transaction.REFUND)
        self.assertEqual(response.status_code, 200)

    @vcr.use_cassette(os.path.join(VCR_DIR, 'stripe_webhook_refund_idempotence.yaml'))
    def test_events_should_be_processed_exactly_once(self):
        response1 = self.view(self.request)
        response2 = self.view(self.request)

        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        Transaction.objects.get(related_transaction=self.txn,
                                transaction_type=Transaction.REFUND)
