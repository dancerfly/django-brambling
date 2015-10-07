from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, RequestFactory

from brambling.models import Attendee
from brambling.tests.factories import (
    EventFactory,
    OrderFactory,
    AttendeeFactory,
    ItemFactory,
    ItemOptionFactory,
    TransactionFactory,
)
from brambling.views.organizer import EventSummaryView


class EventSummaryTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_attendee_count__no_housing(self):
        """Attendee count should be present & accurate; housing data shouldn't."""
        event = EventFactory(collect_housing_data=False)
        order = OrderFactory(event=event)
        transaction = TransactionFactory(event=event, order=order)
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)

        order.add_to_cart(item_option)
        order.add_to_cart(item_option)
        order.mark_cart_paid(transaction)

        AttendeeFactory(order=order, bought_items=order.bought_items.all())

        view = EventSummaryView()
        view.request = self.factory.get('/')
        view.request.user = AnonymousUser()
        view.event = event
        context_data = view.get_context_data()

        self.assertEqual(context_data['attendee_count'], 1)
        self.assertNotIn('attendee_requesting_count', context_data)
        self.assertNotIn('attendee_arranged_count', context_data)
        self.assertNotIn('attendee_home_count', context_data)

    def test_attendee_count__requesting_housing(self):
        """Attendee count should be present & accurate; housing data should."""
        event = EventFactory(collect_housing_data=True)
        order = OrderFactory(event=event)
        transaction = TransactionFactory(event=event, order=order)
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)

        order.add_to_cart(item_option)
        order.add_to_cart(item_option)
        order.mark_cart_paid(transaction)

        AttendeeFactory(
            order=order,
            bought_items=order.bought_items.all(),
            housing_status=Attendee.NEED,
        )

        view = EventSummaryView()
        view.request = self.factory.get('/')
        view.request.user = AnonymousUser()
        view.event = event
        context_data = view.get_context_data()

        self.assertEqual(context_data['attendee_count'], 1)
        self.assertEqual(context_data['attendee_requesting_count'], 1)
        self.assertEqual(context_data['attendee_arranged_count'], 0)
        self.assertEqual(context_data['attendee_home_count'], 0)

    def test_attendee_count__have_housing(self):
        """Attendee count should be present & accurate; housing data should."""
        event = EventFactory(collect_housing_data=True)
        order = OrderFactory(event=event)
        transaction = TransactionFactory(event=event, order=order)
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)

        order.add_to_cart(item_option)
        order.add_to_cart(item_option)
        order.mark_cart_paid(transaction)

        AttendeeFactory(
            order=order,
            bought_items=order.bought_items.all(),
            housing_status=Attendee.HAVE,
        )

        view = EventSummaryView()
        view.request = self.factory.get('/')
        view.request.user = AnonymousUser()
        view.event = event
        context_data = view.get_context_data()

        self.assertEqual(context_data['attendee_count'], 1)
        self.assertEqual(context_data['attendee_requesting_count'], 0)
        self.assertEqual(context_data['attendee_arranged_count'], 1)
        self.assertEqual(context_data['attendee_home_count'], 0)

    def test_attendee_count__home_housing(self):
        """Attendee count should be present & accurate; housing data should."""
        event = EventFactory(collect_housing_data=True)
        order = OrderFactory(event=event)
        transaction = TransactionFactory(event=event, order=order)
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)

        order.add_to_cart(item_option)
        order.add_to_cart(item_option)
        order.mark_cart_paid(transaction)

        AttendeeFactory(
            order=order,
            bought_items=order.bought_items.all(),
            housing_status=Attendee.HOME,
        )

        view = EventSummaryView()
        view.request = self.factory.get('/')
        view.request.user = AnonymousUser()
        view.event = event
        context_data = view.get_context_data()

        self.assertEqual(context_data['attendee_count'], 1)
        self.assertEqual(context_data['attendee_requesting_count'], 0)
        self.assertEqual(context_data['attendee_arranged_count'], 0)
        self.assertEqual(context_data['attendee_home_count'], 1)
