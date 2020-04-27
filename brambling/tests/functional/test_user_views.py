from django.core.urlresolvers import reverse
from django.test import TestCase

from brambling.tests.factories import PersonFactory


class BillingViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.password = 'password'
        cls.person = PersonFactory(password=cls.password)
        super(BillingViewTestCase, cls).setUpTestData()

    def test_anonymous_user_redirected_to_login(self):
        response = self.client.get('/billing/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response['Location'],
            '{}?next=/billing/'.format(reverse('login')),
        )

    def test_authenticated_user_gets_billing_settings(self):
        self.client.login(
            username=self.person.email,
            password=self.password,
        )
        response = self.client.get('/billing/')
        self.assertEqual(response.status_code, 200)
        response.render()
        self.assertIn('Billing settings', response.content)
