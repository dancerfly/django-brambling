from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import Http404
from django.test import TestCase, RequestFactory

from brambling.models import Transaction, EventHousing, Order
from brambling.tests.factories import (
    TransactionFactory,
    EventHousingFactory,
    PersonFactory,
    EventFactory,
    OrderFactory,
    AttendeeFactory,
    ItemFactory,
    ItemOptionFactory,
    OrganizationFactory,
)
from brambling.views.user import MergeOrderView

class MergeOrderViewTestCase(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.view = MergeOrderView()
        self.view.request = self.factory.post('/', {})

    def test_should_be_not_found_if_user_not_authenticated(self):
        self.view.request.user = AnonymousUser()

        with self.assertRaises(Http404):
            response = self.view.post(self.view.request)

    def test_should_be_not_found_if_user_not_confirmed(self):
        self.view.request.user = PersonFactory(confirmed_email='')

        with self.assertRaises(Http404):
            response = self.view.post(self.view.request)


class MergeClaimableOrderTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.view = MergeOrderView()
        self.view.request = self.factory.post('/', {'pk': '444'})
        self.view.request.user = PersonFactory()

    def test_should_be_not_found_if_order_claimable_or_does_not_exist(self):
        with self.assertRaises(Http404):
            response = self.view.post(self.view.request)


class MergeUnclaimableOrderTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.view = MergeOrderView()

        event = EventFactory(collect_housing_data=True)
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)

        self.person = PersonFactory()
        self.order1 = OrderFactory(event=event, person=self.person)
        self.order2 = OrderFactory(event=event, person=None,
                                   email=self.person.email)

        self.tr1 = TransactionFactory(event=event, order=self.order1)
        self.tr2 = TransactionFactory(event=event, order=self.order2)

        self.order1.add_to_cart(item_option)
        self.order1.mark_cart_paid(self.tr1)

        self.order2.add_to_cart(item_option)
        self.order2.add_to_cart(item_option)
        self.order2.mark_cart_paid(self.tr2)

        self.att1 = AttendeeFactory(
            order=self.order1, bought_items=self.order1.bought_items.all(),
            email='attendee1@example.com')
        self.att2 = AttendeeFactory(
            order=self.order2, bought_items=self.order2.bought_items.all(),
            email='attendee1@example.com')

        self.housing1 = EventHousingFactory(
            event=event, order=self.order1, contact_name='Riker',
            contact_email='riker@example.com', contact_phone='111-111-1111',
            public_transit_access=True, person_prefer='Troi',
            person_avoid='Worf')

        self.housing2 = EventHousingFactory(
            event=event, order=self.order2, contact_name='Picard',
            contact_email='jeanluc@example.com', contact_phone='111-111-1111',
            public_transit_access=True, person_prefer='Dr. Crusher',
            person_avoid='Wesley Crusher')

        self.attendee1 = AttendeeFactory(order=self.order1)
        self.attendee2 = AttendeeFactory(order=self.order2)

        self.view.request = self.factory.post('/', {'pk': self.order2.pk})
        self.view.request.user = self.person

        setattr(self.view.request, 'session', 'session')
        messages = FallbackStorage(self.view.request)
        setattr(self.view.request, '_messages', messages)

    def test_should_redirect(self):
        response = self.view.post(self.view.request)

        self.assertEqual(response.status_code, 302)

    def test_should_transfer_transactions_to_new_order(self):
        response = self.view.post(self.view.request)

        self.tr2 = Transaction.objects.get(pk=self.tr2.pk)
        self.assertEqual(self.tr2.order, self.order1)

    def test_should_transfer_bought_items_to_new_order(self):
        response = self.view.post(self.view.request)

        self.assertEqual(self.order1.bought_items.count(), 3)
        for item in self.tr2.bought_items.all():
            self.assertEqual(item.attendee, None)
            self.assertEqual(item.order, self.order1)

    def test_should_delete_old_order(self):
        response = self.view.post(self.view.request)

        with self.assertRaises(Order.DoesNotExist):
            Order.objects.get(pk=self.order2.pk)
