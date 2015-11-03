# encoding: utf-8
from django.test import TestCase, RequestFactory

from brambling.api.v1.views import AttendeeViewSet, BoughtItemViewSet
from brambling.tests.factories import (
    EventFactory,
    OrderFactory,
    AttendeeFactory,
    PersonFactory,
    ItemFactory,
    ItemOptionFactory,
)


class AttendeeViewSetTestCase(TestCase):
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
        event.additional_editors.add(editor1)
        event.additional_editors.add(editor2)
        event.additional_editors.add(editor3)
        order = OrderFactory(event=event, person=person)
        att1 = AttendeeFactory(order=order)
        att2 = AttendeeFactory(order=order)
        att3 = AttendeeFactory(order=order)

        viewset = AttendeeViewSet()
        viewset.request = self.factory.get('/')
        viewset.request.user = person

        qs = viewset.get_queryset()
        self.assertEqual(len(qs), 3)
        self.assertEqual(set(qs), set((att1, att2, att3)))


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
        event.additional_editors.add(editor1)
        event.additional_editors.add(editor2)
        event.additional_editors.add(editor3)
        order = OrderFactory(event=event, person=person)
        att1 = AttendeeFactory(order=order)
        att2 = AttendeeFactory(order=order)
        att3 = AttendeeFactory(order=order)

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
