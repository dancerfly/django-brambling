from decimal import Decimal

from django.conf import settings
from django.test import TestCase

from brambling.models import Event, Transaction
from brambling.tests.factories import EventFactory, PersonFactory, OrderFactory
from brambling.utils.payment import (dwolla_prep, dwolla_is_connected,
                                     dwolla_charge, dwolla_refund)


CHARGE_DATA = {
    u'Amount': 42.15,
    u'ClearingDate': u'',
    u'Date': u'2015-01-31T02:41:38Z',
    u'Destination': {u'Id': u'812-158-1368',
                     u'Image': u'http://uat.dwolla.com/avatars/812-158-1368',
                     u'Name': u'Blah blah blah',
                     u'Type': u'Dwolla'},
    u'DestinationId': u'812-158-1368',
    u'DestinationName': u'Blah blah blah',
    u'Fees': [{u'Amount': 0.25, u'Id': 827529, u'Type': u'Dwolla Fee'},
              {u'Amount': 0.01, u'Id': 827530, u'Type': u'Facilitator Fee'}],
    u'Id': 827527,
    u'Metadata': None,
    u'Notes': u'',
    u'OriginalTransactionId': None,
    u'Source': {u'Id': u'812-743-0925',
                u'Image': u'http://uat.dwolla.com/avatars/812-743-0925',
                u'Name': u'John Doe',
                u'Type': u'Dwolla'},
    u'SourceId': u'812-743-0925',
    u'SourceName': u'John Doe',
    u'Status': u'processed',
    u'Type': u'money_received',
    u'UserType': u'Dwolla'
}


class DwollaChargeTestCase(TestCase):
    def test_dwolla_charge__user(self):
        event = EventFactory(api_type=Event.TEST,
                             application_fee_percent=2.5)
        self.assertTrue(dwolla_is_connected(event, Event.TEST))
        dwolla_prep(Event.TEST)

        person = PersonFactory()
        charge = dwolla_charge(person, 42.15, event, settings.DWOLLA_TEST_USER_PIN)

        self.assertIsInstance(charge, dict)
        self.assertEqual(charge["Type"], "money_received")
        self.assertEqual(len(charge['Fees']), 2)

        txn = Transaction.from_dwolla_charge(charge)
        # 42.15 * 0.025 = 1.05
        self.assertEqual(Decimal(txn.application_fee), Decimal('1.05'))
        # 0.25
        self.assertEqual(Decimal(txn.processing_fee), Decimal('0.25'))

        refund = dwolla_refund(event, txn.remote_id, txn.amount, settings.DWOLLA_TEST_EVENT_PIN)

        self.assertIsInstance(refund, dict)
        self.assertEqual(refund["Amount"], txn.amount)

        refund_txn = Transaction.from_dwolla_refund(refund, txn)
        self.assertEqual(refund_txn.amount, txn.amount)
        self.assertEqual(refund_txn.application_fee, 0)
        self.assertEqual(refund_txn.processing_fee, 0)
