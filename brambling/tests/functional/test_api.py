# encoding: utf-8
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, RequestFactory

from brambling.api.v1.views import AttendeeViewSet
from brambling.models import Attendee
from brambling.tests.factories import (
    EventFactory,
    OrderFactory,
    AttendeeFactory,
    PersonFactory,
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
