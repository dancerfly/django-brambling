from django.contrib.sites.models import Site
from django.core import mail

from django.test import TestCase

from brambling.tests.factories import InviteFactory, EventFactory


class InviteTestCase(TestCase):
    def test_subject__editor(self):
        event = EventFactory()
        invite = InviteFactory(content_id=event.pk)
        self.assertEqual(len(mail.outbox), 0)
        invite.send(Site('test.com', 'test.com'), content=event)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "{} has invited you to edit {}".format(invite.user.get_full_name(), event.name))
