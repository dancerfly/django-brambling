# encoding: utf-8
from django.contrib.auth.models import AnonymousUser
from django.core import mail
from django.test import TestCase, RequestFactory
from django.utils import timezone

from brambling.tests.factories import (
    EventFactory,
    OrderFactory,
    AttendeeFactory,
    ItemFactory,
    ItemOptionFactory,
    TransactionFactory,
    OrganizationFactory,
    DiscountFactory,
)
from brambling.views.orders import SummaryView


class SummaryViewTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_payment__sends_email(self):
        """A successful payment should send a receipt email and an alert email."""
        organization = OrganizationFactory(check_payment_allowed=True)
        event = EventFactory(
            collect_housing_data=False,
            organization=organization,
            check_postmark_cutoff=timezone.now().date(),
        )
        order = OrderFactory(event=event)
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)

        order.add_to_cart(item_option)
        order.add_to_cart(item_option)

        view = SummaryView()
        view.request = self.factory.post('/', {
            'check': 1
        })
        view.request.user = AnonymousUser()
        view.event = event
        view.order = order

        self.assertEqual(len(mail.outbox), 0)
        response = view.post(view.request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 2)

    def test_comped__sends_email(self):
        """A successful completion with fully-comped items should send a receipt email and an alert email."""
        organization = OrganizationFactory()
        event = EventFactory(
            collect_housing_data=False,
            organization=organization,
        )
        order = OrderFactory(event=event)
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)
        discount = DiscountFactory(amount=100, discount_type='percent', event=event, item_options=[item_option])

        order.add_to_cart(item_option)
        order.add_to_cart(item_option)
        order.add_discount(discount)

        view = SummaryView()
        view.request = self.factory.post('/')
        view.request.user = AnonymousUser()
        view.event = event
        view.order = order

        self.assertEqual(len(mail.outbox), 0)
        response = view.post(view.request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 2)
