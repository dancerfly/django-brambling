from decimal import Decimal
from unittest import TestCase

import mock

from brambling.utils.payment import get_fee


class GetFeeTestCase(TestCase):
    def test_get_fee__decimal(self):
        event = mock.MagicMock(application_fee_percent=Decimal('3.33'))
        amount = Decimal('10.00')
        fee = get_fee(event, amount)
        self.assertIsInstance(fee, Decimal)
        self.assertEqual(fee, Decimal('0.33'))

    def test_get_fee__int(self):
        event = mock.MagicMock(application_fee_percent=Decimal('3.33'))
        amount = 10
        fee = get_fee(event, amount)
        self.assertIsInstance(fee, Decimal)
        self.assertEqual(fee, Decimal('0.33'))

    def test_get_fee__float(self):
        event = mock.MagicMock(application_fee_percent=Decimal('3.33'))
        amount = 10.0
        fee = get_fee(event, amount)
        self.assertIsInstance(fee, Decimal)
        self.assertEqual(fee, Decimal('0.33'))
