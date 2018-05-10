# encoding: utf-8
from django.test import TestCase, RequestFactory

from brambling.api.v1.endpoints.boughtitem import BoughtItemViewSet
from brambling.models import EventMember
from brambling.tests.factories import (
    EventFactory,
    OrderFactory,
    AttendeeFactory,
    PersonFactory,
    ItemFactory,
    ItemOptionFactory,
)


class BoughtItemViewSetTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_queryset_distinct(self):
        """
        For authenticated users, make sure the qs is distinct.
        Specifically, having multiple additional editors on
        the event shouldn't cause duplication issues.
        """
        person = PersonFactory()
        editor1 = PersonFactory()
        editor2 = PersonFactory()
        editor3 = PersonFactory()
        event = EventFactory(collect_housing_data=False)
        EventMember.objects.create(
            person=editor1,
            event=event,
            role=EventMember.EDIT,
        )
        EventMember.objects.create(
            person=editor2,
            event=event,
            role=EventMember.EDIT,
        )
        EventMember.objects.create(
            person=editor3,
            event=event,
            role=EventMember.EDIT,
        )
        order = OrderFactory(event=event, person=person)
        # Set up three attendees to trigger duplication.
        AttendeeFactory(order=order)
        AttendeeFactory(order=order)
        AttendeeFactory(order=order)

        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)

        order.add_to_cart(item_option)
        order.add_to_cart(item_option)

        viewset = BoughtItemViewSet()
        viewset.request = self.factory.get('/')
        viewset.request.user = person

        qs = viewset.get_queryset()
        self.assertEqual(len(qs), 2)
        self.assertEqual(set(qs), set(order.bought_items.all()))
