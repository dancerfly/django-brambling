from decimal import Decimal

from django.conf import settings
from django.test import TestCase
from dwolla import transactions

from brambling.models import Event, Transaction
from brambling.tests.factories import EventFactory, PersonFactory, OrderFactory
from brambling.utils.payment import dwolla_prep, dwolla_charge, dwolla_refund, dwolla_get_token


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
                             application_fee_percent=Decimal('2.5'))
        self.assertTrue(event.dwolla_connected())
        dwolla_prep(Event.TEST)

        person = PersonFactory()
        order = OrderFactory(person=person, event=event)
        charge = dwolla_charge(
            sender=person,
            amount=42.15,
            order=order,
            event=event,
            pin=settings.DWOLLA_TEST_USER_PIN,
            source='Balance',
        )

        self.assertIsInstance(charge, dict)
        self.assertEqual(charge["Type"], "money_received")
        self.assertEqual(len(charge['Fees']), 2)
        self.assertEqual(charge["Notes"], "Order {} for {}".format(order.code, event.name))

        txn = Transaction.from_dwolla_charge(charge, event=event)
        # 42.15 * 0.025 = 1.05
        self.assertEqual(Decimal(txn.application_fee), Decimal('1.05'))
        # 0.25
        self.assertEqual(Decimal(txn.processing_fee), Decimal('0.25'))

        refund = dwolla_refund(
            order=order,
            event=event,
            payment_id=txn.remote_id,
            amount=txn.amount,
            pin=settings.DWOLLA_TEST_ORGANIZATION_PIN
        )

        self.assertIsInstance(refund, dict)
        self.assertEqual(refund["Amount"], txn.amount)

        refund_info = transactions.info(
            tid=str(refund['TransactionId']),
            alternate_token=dwolla_get_token(event.organization, event.api_type)
        )
        self.assertEqual(refund_info["Notes"], "Order {} for {}".format(order.code, event.name))

        refund_txn = Transaction.from_dwolla_refund(refund, txn, event=event)
        self.assertEqual(refund_txn.amount, -1 * txn.amount)
        self.assertEqual(refund_txn.application_fee, 0)
        self.assertEqual(refund_txn.processing_fee, 0)
