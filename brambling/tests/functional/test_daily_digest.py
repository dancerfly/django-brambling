# encoding: utf-8
from django.core import mail
from django.test import TestCase
from mock import patch, MagicMock

from brambling.management.commands.send_daily_emails import Command
from brambling.models import Person, Transaction
from brambling.tests.factories import (
    PersonFactory,
    OrganizationFactory,
    EventFactory,
    TransactionFactory,
)


class DailyDigestCommandTestCase(TestCase):
    def setUp(self):
        self.command = Command()

    def test_get_recipients(self):
        person1 = PersonFactory(notify_new_purchases=Person.NOTIFY_NEVER)
        person2 = PersonFactory(notify_new_purchases=Person.NOTIFY_EACH)
        person3 = PersonFactory(notify_new_purchases=Person.NOTIFY_DAILY)
        self.assertEqual(list(self.command.get_recipients()), [person3])

    def test_send_digest__owner__one_event(self):
        owner = PersonFactory(notify_new_purchases=Person.NOTIFY_DAILY)
        organization = OrganizationFactory(owner=owner)
        event = EventFactory(organization=organization)
        transaction = TransactionFactory(event=event, transaction_type=Transaction.PURCHASE)
        self.assertEqual(len(mail.outbox), 0)
        self.command.send_digest(owner)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, '[Dancerfly] New purchases for your events!')
        self.assertIn(event.name, mail.outbox[0].body)
        self.assertIn(event.name, mail.outbox[0].alternatives[0][0])

    def test_send_digest__owner__two_events(self):
        owner = PersonFactory(notify_new_purchases=Person.NOTIFY_DAILY)
        organization = OrganizationFactory(owner=owner)
        event1 = EventFactory(organization=organization)
        event2 = EventFactory(organization=organization)
        transaction1 = TransactionFactory(event=event1, transaction_type=Transaction.PURCHASE)
        transaction2 = TransactionFactory(event=event2, transaction_type=Transaction.PURCHASE)
        self.assertEqual(len(mail.outbox), 0)
        self.command.send_digest(owner)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, '[Dancerfly] New purchases for your events!')
        self.assertIn(event1.name, mail.outbox[0].body)
        self.assertIn(event1.name, mail.outbox[0].alternatives[0][0])
        self.assertIn(event2.name, mail.outbox[0].body)
        self.assertIn(event2.name, mail.outbox[0].alternatives[0][0])

    def test_send_digest__org_editor(self):
        editor = PersonFactory(notify_new_purchases=Person.NOTIFY_DAILY)
        event = EventFactory()
        event.organization.editors.add(editor)
        transaction = TransactionFactory(event=event, transaction_type=Transaction.PURCHASE)
        self.assertEqual(len(mail.outbox), 0)
        self.command.send_digest(editor)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, '[Dancerfly] New purchases for your events!')
        self.assertIn(event.name, mail.outbox[0].body)
        self.assertIn(event.name, mail.outbox[0].alternatives[0][0])

    def test_send_digest__event_editor(self):
        editor = PersonFactory(notify_new_purchases=Person.NOTIFY_DAILY)
        event = EventFactory()
        event.additional_editors.add(editor)
        transaction = TransactionFactory(event=event, transaction_type=Transaction.PURCHASE)
        self.assertEqual(len(mail.outbox), 0)
        self.command.send_digest(editor)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, '[Dancerfly] New purchases for your events!')
        self.assertIn(event.name, mail.outbox[0].body)
        self.assertIn(event.name, mail.outbox[0].alternatives[0][0])

    def test_full_send_and_timestamp(self):
        owner = PersonFactory(notify_new_purchases=Person.NOTIFY_DAILY)
        editor = PersonFactory(notify_new_purchases=Person.NOTIFY_DAILY)
        organization = OrganizationFactory(owner=owner)
        organization.editors.add(editor)
        event = EventFactory(organization=organization)
        transaction = TransactionFactory(event=event, transaction_type=Transaction.PURCHASE)
        self.assertEqual(len(mail.outbox), 0)
        self.command.handle()
        self.assertEqual(len(mail.outbox), 2)

        self.assertEqual(mail.outbox[0].subject, '[Dancerfly] New purchases for your events!')
        self.assertIn(event.name, mail.outbox[0].body)
        self.assertIn(event.name, mail.outbox[0].alternatives[0][0])
        self.assertEqual(mail.outbox[1].subject, '[Dancerfly] New purchases for your events!')
        self.assertIn(event.name, mail.outbox[1].body)
        self.assertIn(event.name, mail.outbox[1].alternatives[0][0])

        owner = Person.objects.get(pk=owner.pk)
        self.assertIsNotNone(owner.last_new_purchases_digest_sent)
        editor = Person.objects.get(pk=editor.pk)
        self.assertIsNotNone(editor.last_new_purchases_digest_sent)

    @patch('brambling.management.commands.send_daily_emails.Command.send_digest')
    def test_full_send_handles_errors(self, send_digest):
        send_digest.side_effect = Exception
        self.command.stderr = MagicMock()
        owner = PersonFactory(notify_new_purchases=Person.NOTIFY_DAILY)
        editor = PersonFactory(notify_new_purchases=Person.NOTIFY_DAILY)
        organization = OrganizationFactory(owner=owner)
        organization.editors.add(editor)
        event = EventFactory(organization=organization)
        transaction = TransactionFactory(event=event, transaction_type=Transaction.PURCHASE)
        self.assertEqual(len(mail.outbox), 0)
        self.command.handle()
        # stderr.write called four times: message & traceback per error.
        self.assertEqual(self.command.stderr.write.call_count, 4)
        self.assertEqual(len(mail.outbox), 0)
