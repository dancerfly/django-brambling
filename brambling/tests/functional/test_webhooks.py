import json

from django.core.exceptions import SuspiciousOperation
from django.core.urlresolvers import reverse
from django.http import Http404
from django.test import Client, TestCase, RequestFactory
import mock

from brambling.models import Transaction
from brambling.tests.factories import TransactionFactory
from brambling.views.payment import DwollaWebhookView, webhooks


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
