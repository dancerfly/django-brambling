from unittest import TestCase

from django.core.exceptions import ValidationError

from brambling.utils.international import clean_postal_code


class PostalCodeTestCase(TestCase):
    def test_gb_postal__valid1(self):
        clean_postal_code('GB', 'NW4 9BX')

    def test_gb_postal__valid2(self):
        clean_postal_code('GB', 'M32 8BR')

    def test_gb_postal__valid3(self):
        clean_postal_code('GB', 'M3 3BT')

    def test_gb_postal__invalid1(self):
        with self.assertRaises(ValidationError):
            clean_postal_code('GB', '12345')

    def test_gb_postal__empty(self):
        clean_postal_code('US', '')

    def test_us_postal__valid1(self):
        clean_postal_code('US', '16801')

    def test_us_postal__valid2(self):
        clean_postal_code('US', '16801-2345')

    def test_us_postal__invalid1(self):
        with self.assertRaises(ValidationError):
            clean_postal_code('US', 'ABCDEF')

    def test_us_postal__empty(self):
        clean_postal_code('US', '')

    def test_unhandled_country(self):
        clean_postal_code('12', ';[]32adf,,,')
