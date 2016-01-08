from django.contrib.sites.models import Site
from django.core import mail
from django.core.exceptions import ValidationError
from django.forms.models import model_to_dict
from django.test import TestCase, RequestFactory

from brambling.forms.organizer import EventForm
from brambling.models import Invite
from brambling.tests.factories import (InviteFactory, EventFactory,
                                       OrderFactory, TransactionFactory,
                                       ItemFactory, OrganizationFactory,
                                       PersonFactory, ItemOptionFactory)
from brambling.views.core import InviteAcceptView


class InviteTestCase(TestCase):
    def test_subject__event_editor(self):
        event = EventFactory()
        invite = InviteFactory(content_id=event.pk)
        self.assertEqual(len(mail.outbox), 0)
        invite.send(Site('test.com', 'test.com'), content=invite.get_content())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "{} has invited you to edit {}".format(invite.user.get_full_name(), event.name))

    def test_subject__event_editor_apostrophe(self):
        event = EventFactory(name="James's Test Event")
        invite = InviteFactory(content_id=event.pk, user=PersonFactory(first_name="Conan",last_name="O'Brien"))
        self.assertEqual(len(mail.outbox), 0)
        invite.send(Site('test.com', 'test.com'), content=invite.get_content())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "{} has invited you to edit {}".format(invite.user.get_full_name(), event.name))

    def test_subject__organization_editor(self):
        event = EventFactory()
        invite = InviteFactory(content_id=event.organization.pk, kind=Invite.ORGANIZATION_EDITOR)
        self.assertEqual(len(mail.outbox), 0)
        invite.send(Site('test.com', 'test.com'), content=invite.get_content())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "{} has invited you to help manage {}".format(invite.user.get_full_name(),
                                                                                               event.organization.name))

    def test_subject__organization_editor_apostrophe(self):
        event = EventFactory(organization=OrganizationFactory(name="Conan's Show"))
        invite = InviteFactory(content_id=event.organization.pk, kind=Invite.ORGANIZATION_EDITOR, user=PersonFactory(first_name="Conan",
                                                                                                                     last_name="O'Brien"))
        self.assertEqual(len(mail.outbox), 0)
        invite.send(Site('test.com', 'test.com'), content=invite.get_content())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "{} has invited you to help manage {}".format(invite.user.get_full_name(),
                                                                                               event.organization.name))

    def test_subject__event(self):
        event = EventFactory(name="Conan's Show")
        invite = InviteFactory(content_id=event.pk, kind=Invite.EVENT)
        content = invite.get_content()
        self.assertEqual(len(mail.outbox), 0)
        invite.send(Site('test.com', 'test.com'), content=invite.get_content())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "You've been invited to attend {}!".format(content.name))

    def test_subject__transfer(self):
        event = EventFactory()
        self.person = PersonFactory()
        event = EventFactory()
        self.order = OrderFactory(event=event, person=self.person)
        transaction = TransactionFactory(event=event, order=self.order, amount=130)
        item = ItemFactory(event=event, name='Multipass')
        item_option1 = ItemOptionFactory(price=100, item=item, name='Gold')
        self.order.add_to_cart(item_option1)
        boughtitem = self.order.bought_items.all()[0]
        invite = InviteFactory(content_id=boughtitem.pk, kind=Invite.TRANSFER, user=PersonFactory(first_name="Conan",
                                                                                                  last_name="O'Brien"))
        invite.send(Site('test.com', 'test.com'), content=invite.get_content())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "{} wants to transfer an item to you".format(invite.user.get_full_name()))

class EventFormTestCase(TestCase):
    def test_clean_invite_attendees__valid(self):
        expected = ['test@test.te', 'test@demo.com']
        data = ','.join(expected)
        org = OrganizationFactory()
        form = EventForm(None, org, False)
        form.cleaned_data = {'invite_attendees': data}
        cleaned = form.clean_invite_attendees()
        self.assertEqual(cleaned, expected)

    def test_clean_invite_attendees__strip_whitespace(self):
        expected = ['test@test.te', 'test@demo.com']
        data = ', '.join(expected)
        org = OrganizationFactory()
        form = EventForm(None, org, False)
        form.cleaned_data = {'invite_attendees': data}
        cleaned = form.clean_invite_attendees()
        self.assertEqual(cleaned, expected)

    def test_clean_invite_attendees__invalid(self):
        expected = ['test@test.te', 'test@democom']
        data = ','.join(expected)
        org = OrganizationFactory()
        form = EventForm(None, org, False)
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
        form = EventForm(
            request,
            event.organization,
            False,
            instance=event,
            data=data
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.cleaned_data.get('invite_attendees'))
        self.assertEqual(event.get_invites().count(), 0)
        self.assertEqual(len(mail.outbox), 0)
        form.save()
        self.assertEqual(event.get_invites().count(), 2)
        self.assertEqual(len(mail.outbox), 2)


class InviteAcceptViewTestCase(TestCase):
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
