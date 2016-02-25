from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from brambling.models import (
    EventMember,
    OrganizationMember,
)
from brambling.tests.factories import (
    EventFactory,
    OrganizationFactory,
    PersonFactory,
)


class EventPermissionsTestCase(TestCase):
    def test_organization__owner(self):
        person = PersonFactory()
        event = EventFactory()
        OrganizationMember.objects.create(
            person=person,
            organization=event.organization,
            role=OrganizationMember.OWNER,
        )
        with self.assertNumQueries(1):
            self.assertEqual(
                person.get_all_permissions(event),
                set(('view', 'edit', 'change_permissions')),
            )
        with self.assertNumQueries(0):
            self.assertTrue(person.has_perm('view', event))
            self.assertTrue(person.has_perm('edit', event))
            self.assertTrue(person.has_perm('change_permissions', event))

    def test_organization__edit(self):
        person = PersonFactory()
        event = EventFactory()
        OrganizationMember.objects.create(
            person=person,
            organization=event.organization,
            role=OrganizationMember.EDIT,
        )
        with self.assertNumQueries(1):
            self.assertEqual(
                person.get_all_permissions(event),
                set(('view', 'edit', 'change_permissions')),
            )
        with self.assertNumQueries(0):
            self.assertTrue(person.has_perm('view', event))
            self.assertTrue(person.has_perm('edit', event))
            self.assertTrue(person.has_perm('change_permissions', event))

    def test_organization__view(self):
        person = PersonFactory()
        event = EventFactory()
        OrganizationMember.objects.create(
            person=person,
            organization=event.organization,
            role=OrganizationMember.VIEW,
        )
        with self.assertNumQueries(2):
            self.assertEqual(
                person.get_all_permissions(event),
                set(('view',)),
            )
        with self.assertNumQueries(0):
            self.assertTrue(person.has_perm('view', event))
            self.assertFalse(person.has_perm('edit', event))
            self.assertFalse(person.has_perm('change_permissions', event))

    def test_organization__view__event__edit(self):
        """Max permission level takes precedence."""
        person = PersonFactory()
        event = EventFactory()
        OrganizationMember.objects.create(
            person=person,
            organization=event.organization,
            role=OrganizationMember.VIEW,
        )
        EventMember.objects.create(
            person=person,
            event=event,
            role=EventMember.EDIT,
        )
        with self.assertNumQueries(2):
            self.assertEqual(
                person.get_all_permissions(event),
                set(('view', 'edit')),
            )
        with self.assertNumQueries(0):
            self.assertTrue(person.has_perm('view', event))
            self.assertTrue(person.has_perm('edit', event))
            self.assertFalse(person.has_perm('change_permissions', event))

    def test_event__edit(self):
        person = PersonFactory()
        event = EventFactory()
        EventMember.objects.create(
            person=person,
            event=event,
            role=EventMember.EDIT,
        )
        with self.assertNumQueries(2):
            self.assertEqual(
                person.get_all_permissions(event),
                set(('view', 'edit')),
            )
        with self.assertNumQueries(0):
            self.assertTrue(person.has_perm('view', event))
            self.assertTrue(person.has_perm('edit', event))
            self.assertFalse(person.has_perm('change_permissions', event))

    def test_event__view(self):
        person = PersonFactory()
        event = EventFactory()
        EventMember.objects.create(
            person=person,
            event=event,
            role=EventMember.VIEW,
        )
        with self.assertNumQueries(2):
            self.assertEqual(
                person.get_all_permissions(event),
                set(('view',)),
            )
        with self.assertNumQueries(0):
            self.assertTrue(person.has_perm('view', event))
            self.assertFalse(person.has_perm('edit', event))
            self.assertFalse(person.has_perm('change_permissions', event))

    def test_not_member(self):
        person = PersonFactory()
        event = EventFactory()
        with self.assertNumQueries(2):
            self.assertEqual(
                person.get_all_permissions(event),
                set(),
            )
        with self.assertNumQueries(0):
            self.assertFalse(person.has_perm('view', event))
            self.assertFalse(person.has_perm('edit', event))
            self.assertFalse(person.has_perm('change_permissions', event))

    def test_anonymous(self):
        person = AnonymousUser()
        event = EventFactory()
        with self.assertNumQueries(0):
            self.assertEqual(
                person.get_all_permissions(event),
                set(),
            )
        with self.assertNumQueries(0):
            self.assertFalse(person.has_perm('view', event))
            self.assertFalse(person.has_perm('edit', event))
            self.assertFalse(person.has_perm('change_permissions', event))

    def test_superuser(self):
        person = PersonFactory(is_superuser=True)
        event = EventFactory()
        with self.assertNumQueries(0):
            self.assertEqual(
                person.get_all_permissions(event),
                set(('view', 'edit', 'change_permissions')),
            )
        with self.assertNumQueries(0):
            self.assertTrue(person.has_perm('view', event))
            self.assertTrue(person.has_perm('edit', event))
            self.assertTrue(person.has_perm('change_permissions', event))


class OrganizationPermissionsTestCase(TestCase):
    def test_organization__owner(self):
        person = PersonFactory()
        event = EventFactory()
        OrganizationMember.objects.create(
            person=person,
            organization=event.organization,
            role=OrganizationMember.OWNER,
        )
        with self.assertNumQueries(1):
            self.assertEqual(
                person.get_all_permissions(event.organization),
                set(('view', 'edit', 'change_permissions')),
            )
        with self.assertNumQueries(0):
            self.assertTrue(person.has_perm('view', event.organization))
            self.assertTrue(person.has_perm('edit', event.organization))
            self.assertTrue(person.has_perm('change_permissions', event.organization))

    def test_organization__edit(self):
        person = PersonFactory()
        event = EventFactory()
        OrganizationMember.objects.create(
            person=person,
            organization=event.organization,
            role=OrganizationMember.EDIT,
        )
        with self.assertNumQueries(1):
            self.assertEqual(
                person.get_all_permissions(event.organization),
                set(('view', 'edit')),
            )
        with self.assertNumQueries(0):
            self.assertTrue(person.has_perm('view', event.organization))
            self.assertTrue(person.has_perm('edit', event.organization))
            self.assertFalse(person.has_perm('change_permissions', event.organization))

    def test_organization__view(self):
        person = PersonFactory()
        event = EventFactory()
        OrganizationMember.objects.create(
            person=person,
            organization=event.organization,
            role=OrganizationMember.VIEW,
        )
        with self.assertNumQueries(1):
            self.assertEqual(
                person.get_all_permissions(event.organization),
                set(('view',)),
            )
        with self.assertNumQueries(0):
            self.assertTrue(person.has_perm('view', event.organization))
            self.assertFalse(person.has_perm('edit', event.organization))
            self.assertFalse(person.has_perm('change_permissions', event.organization))

    def test_event__edit(self):
        person = PersonFactory()
        event = EventFactory()
        EventMember.objects.create(
            person=person,
            event=event,
            role=EventMember.EDIT,
        )
        with self.assertNumQueries(1):
            self.assertEqual(
                person.get_all_permissions(event.organization),
                set(),
            )
        with self.assertNumQueries(0):
            self.assertFalse(person.has_perm('view', event.organization))
            self.assertFalse(person.has_perm('edit', event.organization))
            self.assertFalse(person.has_perm('change_permissions', event.organization))

    def test_event__view(self):
        person = PersonFactory()
        event = EventFactory()
        EventMember.objects.create(
            person=person,
            event=event,
            role=EventMember.VIEW,
        )
        with self.assertNumQueries(1):
            self.assertEqual(
                person.get_all_permissions(event.organization),
                set(),
            )
        with self.assertNumQueries(0):
            self.assertFalse(person.has_perm('view', event.organization))
            self.assertFalse(person.has_perm('edit', event.organization))
            self.assertFalse(person.has_perm('change_permissions', event.organization))

    def test_not_member(self):
        person = PersonFactory()
        event = EventFactory()
        with self.assertNumQueries(1):
            self.assertEqual(
                person.get_all_permissions(event.organization),
                set(),
            )
        with self.assertNumQueries(0):
            self.assertFalse(person.has_perm('view', event.organization))
            self.assertFalse(person.has_perm('edit', event.organization))
            self.assertFalse(person.has_perm('change_permissions', event.organization))

    def test_anonymous(self):
        person = AnonymousUser()
        event = EventFactory()
        with self.assertNumQueries(0):
            self.assertEqual(
                person.get_all_permissions(event.organization),
                set(),
            )
        with self.assertNumQueries(0):
            self.assertFalse(person.has_perm('view', event.organization))
            self.assertFalse(person.has_perm('edit', event.organization))
            self.assertFalse(person.has_perm('change_permissions', event.organization))

    def test_superuser(self):
        person = PersonFactory(is_superuser=True)
        event = EventFactory()
        with self.assertNumQueries(0):
            self.assertEqual(
                person.get_all_permissions(event.organization),
                set(('view', 'edit', 'change_permissions')),
            )
        with self.assertNumQueries(0):
            self.assertTrue(person.has_perm('view', event.organization))
            self.assertTrue(person.has_perm('edit', event.organization))
            self.assertTrue(person.has_perm('change_permissions', event.organization))
