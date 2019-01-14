from unittest import skipUnless
import json
import os

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import Http404
from django.test import Client, TestCase, RequestFactory
import mock
import stripe
import vcr

from brambling.models import (
    ProcessedStripeEvent,
    Transaction,
)
from brambling.payment.stripe.core import stripe_prep
from brambling.payment.stripe.api import stripe_charge, stripe_refund
from brambling.payment.core import TEST
from brambling.tests.factories import (TransactionFactory, OrderFactory,
                                       EventFactory, ItemFactory,
                                       ItemOptionFactory)
from brambling.views.payment import StripeWebhookView


VCR_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


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

    @mock.patch('stripe.Event.retrieve')
    def test_non_refund_event_type(self, event_retrieve):
        non_refund_event = stripe.Event.construct_from({
            'id': 'coupon_1',
            'type': 'coupon.created',
        }, settings.STRIPE_TEST_SECRET_KEY)

        event_retrieve.return_value = non_refund_event
        data = json.dumps(non_refund_event)

        request = self.factory.post('/', content_type='application/json', data=data)
        response = self.view(request)
        self.assertEqual(response.status_code, 200)

    def test_missing_event_id(self):
        data = json.dumps({})

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
        self.data = json.dumps({'id': 'evt_123_event_id'})

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

    @mock.patch('stripe.Charge.retrieve')
    @vcr.use_cassette(os.path.join(VCR_DIR, 'stripe_webhook_charge_not_found.yaml'))
    def test_stripe_charge_not_found(self, charge_retrieve):
        # remote_id = STRIPE_REFUND_EVENT['data']['object']['id']
        self.txn = TransactionFactory(event=self.event, order=self.order,
                                      remote_id='charge_id')
        charge_retrieve.side_effect = stripe.error.InvalidRequestError(
            'not found', 1)

        with self.assertRaises(Http404):
            self.view(self.request)

    @mock.patch('stripe.Event.retrieve')
    def test_transaction_not_found(self, event_retrieve):
        event_retrieve.return_value = stripe.Event.construct_from({
            'id': 'event_1',
            'livemode': False,
            'type': 'charge.refunded',
            'data': {
                'object': {'id': 'charge_id'},
            },
        }, settings.STRIPE_TEST_SECRET_KEY)
        response = self.view(self.request)
        self.assertEqual(response.status_code, 200)
        with self.assertRaises(Transaction.DoesNotExist):
            Transaction.objects.get(remote_id='charge_id')

    @mock.patch('stripe.Event.retrieve')
    def test_charge_id_not_found(self, event_retrieve):
        event_retrieve.return_value = stripe.Event.construct_from({
            'id': 'event_1',
            'livemode': False,
            'type': 'charge.refunded',
            'data': {
                'object': {},
            },
        }, settings.STRIPE_TEST_SECRET_KEY)

        with self.assertRaises(Http404):
            self.view(self.request)


class SuccessfulRefundWebhookTestCase(TestCase):
    @vcr.use_cassette(os.path.join(VCR_DIR, 'stripe_webhook_refund_success.yaml'))
    def setUp(self):
        stripe_prep(TEST)

        self.event = EventFactory()
        self.order = OrderFactory(event=self.event)

        self.factory = RequestFactory()
        self.view = StripeWebhookView.as_view()
        self.stripe_event = {'id': 'evt_123_event_id'}
        self.data = json.dumps(self.stripe_event)

        self.request = self.factory.post(path='/',
                                         content_type='application/json',
                                         data=self.data)

        item = ItemFactory(event=self.event)
        item_option = ItemOptionFactory(price=60, item=item)
        self.order.add_to_cart(item_option)

        token = stripe.Token.create(
            card={
                'number': '4242424242424242',
                'exp_month': 12,
                'exp_year': 2017,
                'cvc': '123'
            },
        )

        charge = stripe_charge(token, 100, self.order, self.event)

        self.txn = Transaction.from_stripe_charge(
            charge,
            event=self.event,
            order=self.order,
            api_type=self.event.api_type,
        )

        self.refund = stripe_refund(self.order, self.event, charge.id, 100)

        data = mock.Mock(object=mock.Mock(name='charge', id=charge.id))
        self.mock_event = mock.Mock(
            data=data,
            type='charge.refunded',
            livemode=False,
        )
        self.order.mark_cart_paid(self.txn)

    @skipUnless(os.environ.get('STRIPE_TEST_APPLICATION_ID'), 'stripe test settings required')
    @mock.patch('stripe.Event.retrieve')
    def test_transaction_refunded_successfully(self, event_retrieve):
        event_retrieve.return_value = self.mock_event
        response = self.view(self.request)

        refund = Transaction.objects.get(
            related_transaction=self.txn,
            transaction_type=Transaction.REFUND,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(refund.amount, -100)
        self.assertEqual(refund.application_fee, -2.5)
        self.assertEqual(refund.method, Transaction.STRIPE)
        self.assertEqual(refund.order, self.order)
        self.assertEqual(refund.event, self.event)

    @skipUnless(os.environ.get('STRIPE_TEST_APPLICATION_ID'), 'stripe test settings required')
    @mock.patch('stripe.Event.retrieve')
    def test_events_should_be_processed_exactly_once(self, event_retrieve):
        event_retrieve.return_value = self.mock_event
        response1 = self.view(self.request)
        response2 = self.view(self.request)

        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        Transaction.objects.get(related_transaction=self.txn,
                                transaction_type=Transaction.REFUND)

    @skipUnless(os.environ.get('STRIPE_TEST_APPLICATION_ID'), 'stripe test settings required')
    @mock.patch('stripe.Event.retrieve')
    def test_events_should_be_processed_exactly_once_in_livemode(self, event_retrieve):
        self.mock_event.livemode = True
        self.txn.api_type = Transaction.LIVE
        self.txn.save()
        event_retrieve.return_value = self.mock_event

        response1 = self.view(self.request)
        response2 = self.view(self.request)

        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        Transaction.objects.get(related_transaction=self.txn,
                                transaction_type=Transaction.REFUND)

    @skipUnless(os.environ.get('STRIPE_TEST_APPLICATION_ID'), 'stripe test settings required')
    @mock.patch('stripe.Event.retrieve')
    def test_events_should_be_logged_in_test_mode(self, event_retrieve):
        event_retrieve.return_value = self.mock_event
        self.view(self.request)
        ProcessedStripeEvent.objects.get(
            api_type=ProcessedStripeEvent.TEST,
            stripe_event_id=self.stripe_event['id'],
        )

    @mock.patch('stripe.Event.retrieve')
    def test_events_should_be_logged_in_live_mode(self, event_retrieve):
        self.mock_event.livemode = True
        event_retrieve.return_value = self.mock_event
        self.view(self.request)
        ProcessedStripeEvent.objects.get(
            api_type=ProcessedStripeEvent.LIVE,
            stripe_event_id=self.stripe_event['id'],
        )
