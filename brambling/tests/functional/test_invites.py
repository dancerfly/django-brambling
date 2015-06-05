from django.contrib.sites.models import Site
from django.core import mail

from django.test import TestCase

from brambling.models import Invite
from brambling.tests.factories import InviteFactory, EventFactory


class InviteTestCase(TestCase):
    def test_subject__event_editor(self):
        event = EventFactory()
        invite = InviteFactory(content_id=event.pk)
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
        self.assertEqual(mail.outbox[0].subject, "{} has invited you to help manage {}".format(invite.user.get_full_name(), event.organization.name))
