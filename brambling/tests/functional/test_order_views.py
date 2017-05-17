# encoding: utf-8
from datetime import timedelta

from django.contrib.auth.models import AnonymousUser
from django.core import mail
from django.test import TestCase, RequestFactory
from django.utils import timezone

from brambling.models import OrganizationMember, BoughtItem
from brambling.tests.factories import (
    EventFactory,
    OrderFactory,
    ItemFactory,
    ItemOptionFactory,
    OrganizationFactory,
    DiscountFactory,
    PersonFactory,
    TransactionFactory,
)
from brambling.views.orders import (
    SummaryView,
    TransferView,
    RegistrationWorkflow,
)


class SummaryViewTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_payment__sends_email(self):
        """A successful payment should send a receipt email and an alert email."""
        organization = OrganizationFactory(check_payment_allowed=True)
        owner = PersonFactory()
        OrganizationMember.objects.create(
            person=owner,
            organization=organization,
            role=OrganizationMember.OWNER,
        )
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
        owner = PersonFactory()
        OrganizationMember.objects.create(
            person=owner,
            organization=organization,
            role=OrganizationMember.OWNER,
        )
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


class TransferViewTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_transfer_item(self):
        """A user should be able to transfer an item on their order to an
        email address."""
        organization = OrganizationFactory(check_payment_allowed=True)
        event_owner = PersonFactory()
        OrganizationMember.objects.create(
            person=event_owner,
            organization=organization,
            role=OrganizationMember.OWNER,
        )
        event = EventFactory(
            collect_housing_data=False,
            organization=organization,
            check_postmark_cutoff=timezone.now().date() + timedelta(1),
        )
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)

        orderer = PersonFactory()
        receiver = PersonFactory()
        order = OrderFactory(
            event=event,
            person=orderer,
        )
        order.add_to_cart(item_option)
        transaction = TransactionFactory(event=event, is_confirmed=True)
        order.mark_cart_paid(transaction)

        # The BoughtItem should be in the correct state if we've set up this
        # test Order correctly.
        self.assertEqual(order.bought_items.first().status, BoughtItem.BOUGHT)

        view = TransferView()
        view.kwargs = dict(
            event_slug=event.slug,
            organization_slug=organization.slug,
        )
        view.request = self.factory.post('/', dict(
            bought_item=order.bought_items.first().pk,
            email=receiver.email,
        ))
        view.request.user = orderer
        view.order = order
        view.workflow = RegistrationWorkflow(order=order, event=event)
        view.current_step = view.workflow.steps.get(view.current_step_slug)
        response = view.post(view.request)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('offered an item transfer', mail.outbox[0].body)

    def test_unauthenticated_transfer_fails(self):
        """Only authenticated users should be allowed to transfer items,
        despite unauthenticated visitors being alloewd to place orders.
        """
        pass

    def test_pending_payment_transfer_fails(self):
        """A transfer on an item with unconfirmed transactions should be prohibited."""
        pass
