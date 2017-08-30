from django.contrib.sessions.middleware import SessionMiddleware
from django.core import mail
from django.core.exceptions import ValidationError
from django.forms.models import model_to_dict
from django.test import TestCase, RequestFactory

from brambling.forms.organizer import EventRegistrationForm
from brambling.models import (
    Invite,
    Order,
)
from brambling.tests.factories import (InviteFactory, EventFactory,
                                       OrderFactory, TransactionFactory,
                                       ItemFactory, OrganizationFactory,
                                       PersonFactory, ItemOptionFactory)
from brambling.utils.invites import (
    EventInvite,
    EventEditInvite,
    EventViewInvite,
    get_invite,
    OrganizationOwnerInvite,
    OrganizationEditInvite,
    OrganizationViewInvite,
    TransferInvite,
)
from brambling.views.invites import InviteAcceptView
import mock


class InviteTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_subject__event_edit(self):
        event = EventFactory()
        request = self.factory.get('/')
        request.user = PersonFactory()
        invite, created = EventEditInvite.get_or_create(
            request=request,
            email='test@test.com',
            content=event,
        )
        self.assertEqual(len(mail.outbox), 0)
        invite.send()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "{} has invited you to collaborate on {}".format(request.user.get_full_name(), event.name))

    def test_subject__event_edit_apostrophe(self):
        event = EventFactory(name="James's Test Event")
        request = self.factory.get('/')
        request.user = PersonFactory(first_name="Conan", last_name="O'Brien")
        invite, created = EventEditInvite.get_or_create(
            request=request,
            email='test@test.com',
            content=event,
        )
        self.assertEqual(len(mail.outbox), 0)
        invite.send()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "{} has invited you to collaborate on {}".format(request.user.get_full_name(), event.name))

    def test_subject__event_view(self):
        event = EventFactory()
        request = self.factory.get('/')
        request.user = PersonFactory()
        invite, created = EventViewInvite.get_or_create(
            request=request,
            email='test@test.com',
            content=event,
        )
        self.assertEqual(len(mail.outbox), 0)
        invite.send()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "{} has invited you to collaborate on {}".format(request.user.get_full_name(), event.name))

    def test_subject__event_view_apostrophe(self):
        event = EventFactory(name="James's Test Event")
        request = self.factory.get('/')
        request.user = PersonFactory(first_name="Conan", last_name="O'Brien")
        invite, created = EventViewInvite.get_or_create(
            request=request,
            email='test@test.com',
            content=event,
        )
        self.assertEqual(len(mail.outbox), 0)
        invite.send()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "{} has invited you to collaborate on {}".format(request.user.get_full_name(), event.name))

    def test_subject__organization_owner(self):
        event = EventFactory()
        request = self.factory.get('/')
        request.user = PersonFactory()
        invite, created = OrganizationOwnerInvite.get_or_create(
            request=request,
            email='test@test.com',
            content=event.organization,
        )
        self.assertEqual(len(mail.outbox), 0)
        invite.send()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "{} has invited you to help manage {}".format(request.user.get_full_name(),
                                                                                               event.organization.name))

    def test_subject__organization_owner_apostrophe(self):
        event = EventFactory(organization=OrganizationFactory(name="Conan's Show"))
        request = self.factory.get('/')
        request.user = PersonFactory(first_name="Conan", last_name="O'Brien")
        invite, created = OrganizationOwnerInvite.get_or_create(
            request=request,
            email='test@test.com',
            content=event.organization,
        )
        self.assertEqual(len(mail.outbox), 0)
        invite.send()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "{} has invited you to help manage {}".format(request.user.get_full_name(),
                                                                                               event.organization.name))

    def test_subject__organization_edit(self):
        event = EventFactory()
        request = self.factory.get('/')
        request.user = PersonFactory()
        invite, created = OrganizationEditInvite.get_or_create(
            request=request,
            email='test@test.com',
            content=event.organization,
        )
        self.assertEqual(len(mail.outbox), 0)
        invite.send()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "{} has invited you to help manage {}".format(request.user.get_full_name(),
                                                                                               event.organization.name))

    def test_subject__organization_edit_apostrophe(self):
        event = EventFactory(organization=OrganizationFactory(name="Conan's Show"))
        request = self.factory.get('/')
        request.user = PersonFactory(first_name="Conan", last_name="O'Brien")
        invite, created = OrganizationEditInvite.get_or_create(
            request=request,
            email='test@test.com',
            content=event.organization,
        )
        self.assertEqual(len(mail.outbox), 0)
        invite.send()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "{} has invited you to help manage {}".format(request.user.get_full_name(),
                                                                                               event.organization.name))

    def test_subject__organization_view(self):
        event = EventFactory()
        request = self.factory.get('/')
        request.user = PersonFactory()
        invite, created = OrganizationViewInvite.get_or_create(
            request=request,
            email='test@test.com',
            content=event.organization,
        )
        self.assertEqual(len(mail.outbox), 0)
        invite.send()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "{} has invited you to help manage {}".format(request.user.get_full_name(),
                                                                                               event.organization.name))

    def test_subject__organization_view_apostrophe(self):
        event = EventFactory(organization=OrganizationFactory(name="Conan's Show"))
        request = self.factory.get('/')
        request.user = PersonFactory(first_name="Conan", last_name="O'Brien")
        invite, created = OrganizationViewInvite.get_or_create(
            request=request,
            email='test@test.com',
            content=event.organization,
        )
        self.assertEqual(len(mail.outbox), 0)
        invite.send()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "{} has invited you to help manage {}".format(request.user.get_full_name(),
                                                                                               event.organization.name))

    def test_subject__event(self):
        event = EventFactory(name="Conan's Show")
        request = self.factory.get('/')
        request.user = PersonFactory()
        invite, created = EventInvite.get_or_create(
            request=request,
            email='test@test.com',
            content=event,
        )
        self.assertEqual(len(mail.outbox), 0)
        invite.send()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "You've been invited to attend {}!".format(event.name))


class EventRegistrationFormTestCase(TestCase):
    def test_clean_invite_attendees__valid(self):
        expected = ['test@test.te', 'test@demo.com']
        data = ','.join(expected)
        org = OrganizationFactory()
        form = EventRegistrationForm(None, org)
        form.cleaned_data = {'invite_attendees': data}
        cleaned = form.clean_invite_attendees()
        self.assertEqual(cleaned, expected)

    def test_clean_invite_attendees__strip_whitespace(self):
        expected = ['test@test.te', 'test@demo.com']
        data = ', '.join(expected)
        org = OrganizationFactory()
        form = EventRegistrationForm(None, org)
        form.cleaned_data = {'invite_attendees': data}
        cleaned = form.clean_invite_attendees()
        self.assertEqual(cleaned, expected)

    def test_clean_invite_attendees__invalid(self):
        expected = ['test@test.te', 'test@democom']
        data = ','.join(expected)
        org = OrganizationFactory()
        form = EventRegistrationForm(None, org)
        form.cleaned_data = {'invite_attendees': data}
        with self.assertRaises(ValidationError):
            form.clean_invite_attendees()

    def test_attendee_invites_on_save(self):
        emails = ['test@test.te', 'test@demo.com']
        event = EventFactory()
        data = model_to_dict(event)
        data['invite_attendees'] = ','.join(emails)
        request = RequestFactory().get('/')
        request.user = PersonFactory()
        form = EventRegistrationForm(
            request,
            event.organization,
            instance=event,
            data=data
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.cleaned_data.get('invite_attendees'))
        self.assertEqual(EventInvite.get_invites(event).count(), 0)
        self.assertEqual(len(mail.outbox), 0)
        form.save()
        self.assertEqual(EventInvite.get_invites(event).count(), 2)
        self.assertEqual(len(mail.outbox), 2)


class InviteAcceptViewTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.session_middleware = SessionMiddleware()

    def _add_session(self, request):
        self.session_middleware.process_request(request)

    def test_context_data__no_invite(self):
        view = InviteAcceptView()
        view.invite = None
        view.content = None
        view.request = RequestFactory().get('/')
        context = view.get_context_data()
        self.assertIsNone(context['invite'])
        self.assertIsNone(context['content'])
        self.assertFalse(context['invited_person_exists'])
        self.assertFalse(context['sender_display'])
        self.assertFalse(context['invited_person_exists'])

    def test_invite(self):
        view = InviteAcceptView()
        event = EventFactory()
        invite = InviteFactory(content_id=event.pk, kind=EventInvite.slug, user=PersonFactory(first_name="Conan", last_name="O'Brien"))
        view.content = event
        view.request = RequestFactory().get('/')
        view.request.user = PersonFactory(email=invite.email, confirmed_email=invite.email)
        self._add_session(view.request)
        with mock.patch.object(wraps=Order.objects.for_request, target=Order.objects, attribute='for_request') as for_request:
            view.get(view.request, code=invite.code)
        for_request.assert_called_once_with(create=True, request=view.request, event=view.content)
        orders = Order.objects.all()
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0].person, view.request.user)


class TransferInviteTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.person = PersonFactory(
            first_name="Conan",
            last_name="O'Brien",
        )
        self.event = EventFactory()
        self.order = OrderFactory(
            event=self.event,
            person=self.person,
        )
        TransactionFactory(
            event=self.event,
            order=self.order,
            amount=130,
        )
        self.item = ItemFactory(
            event=self.event,
            name='Multipass',
        )
        self.item_option1 = ItemOptionFactory(
            price=100,
            item=self.item,
            name='Gold',
        )
        self.order.add_to_cart(self.item_option1)
        self.bought_item = self.order.bought_items.all()[0]

    def test_email_subject__transfer(self):
        request = self.factory.get('/')
        request.user = self.person
        invite, created = TransferInvite.get_or_create(
            request=request,
            email='test@test.com',
            content=self.bought_item,
        )
        invite.send()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            "{} wants to transfer an item to you".format(
                self.person.get_full_name()
            ),
        )

    def test_manage_not_allowed__no_order(self):
        # A person who isn't signed up for the event
        # shouldn't be able to manage it.
        person2 = PersonFactory()
        request = self.factory.get('/')
        request.user = person2

        session_middleware = SessionMiddleware()
        session_middleware.process_request(request)

        instance = Invite.objects.create(
            email=person2.email,
            user=self.person,
            kind='transfer',
            content_id=self.bought_item.id,
        )
        invite = get_invite(request, instance.code, self.bought_item)
        self.assertFalse(invite.manage_allowed())

    def test_manage_not_allowed__wrong_order(self):
        # A person who doesn't have the originating order
        # shouldn't be able to manage it.
        person2 = PersonFactory()
        OrderFactory(
            person=person2,
            event=self.event,
        )
        request = self.factory.get('/')
        request.user = person2

        instance = Invite.objects.create(
            email=person2.email,
            user=self.person,
            kind='transfer',
            content_id=self.bought_item.id,
        )
        invite = get_invite(request, instance.code, self.bought_item)
        self.assertFalse(invite.manage_allowed())

    def test_manage_allowed(self):
        # Owner of a bought item should be able to manage transfer invites.
        person2 = PersonFactory()
        request = self.factory.get('/')
        request.user = self.person

        instance = Invite.objects.create(
            email=person2.email,
            user=self.person,
            kind='transfer',
            content_id=self.bought_item.id,
        )
        invite = get_invite(request, instance.code, self.bought_item)
        self.assertTrue(invite.manage_allowed())
