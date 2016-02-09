from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from brambling.models import Event, OrganizationMember
from brambling.tests.factories import EventFactory, PersonFactory, OrderFactory


class EventModelTestCase(TestCase):
    def tearDown(self):
        OrganizationMember.objects.clear_cache()

    def test_viewable_by__public_published__anon(self):
        event = EventFactory(is_published=True, privacy=Event.PUBLIC)
        person = AnonymousUser()
        self.assertTrue(event.viewable_by(person))

    def test_viewable_by__public_unpublished__anon(self):
        event = EventFactory(is_published=False, privacy=Event.PUBLIC)
        person = AnonymousUser()
        self.assertFalse(event.viewable_by(person))

    def test_viewable_by__public_unpublished__authed(self):
        event = EventFactory(is_published=False, privacy=Event.PUBLIC)
        person = PersonFactory()
        self.assertFalse(event.viewable_by(person))

    def test_viewable_by__public_unpublished__owner(self):
        event = EventFactory(is_published=False, privacy=Event.PUBLIC)
        person = PersonFactory()
        OrganizationMember.objects.create(
            person=person,
            organization=event.organization,
            role=OrganizationMember.OWNER,
        )
        self.assertTrue(event.viewable_by(person))

    def test_viewable_by__invited_published__anon(self):
        event = EventFactory(is_published=True, privacy=Event.INVITED)
        person = AnonymousUser()
        self.assertFalse(event.viewable_by(person))

    def test_viewable_by__invited_published__uninvited(self):
        event = EventFactory(is_published=True, privacy=Event.INVITED)
        person = PersonFactory()
        self.assertFalse(event.viewable_by(person))

    def test_viewable_by__invited_published__invited(self):
        event = EventFactory(is_published=True, privacy=Event.INVITED)
        person = PersonFactory()
        OrderFactory(event=event, person=person)
        self.assertTrue(event.viewable_by(person))
