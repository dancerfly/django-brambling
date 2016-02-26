# encoding: utf-8
from datetime import timedelta

from django.core import mail
from django.test import TestCase
from django.utils import timezone
from mock import patch, MagicMock

from brambling.management.commands.send_daily_emails import Command
from brambling.models import (
    Person,
    Transaction,
    OrganizationMember,
    EventMember,
)
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
        PersonFactory(notify_new_purchases=Person.NOTIFY_NEVER)
        PersonFactory(notify_new_purchases=Person.NOTIFY_EACH)
        recipient = PersonFactory(notify_new_purchases=Person.NOTIFY_DAILY)
        self.assertEqual(list(self.command.get_recipients()), [recipient])

    def test_send_digest__owner__one_event(self):
        owner = PersonFactory(notify_new_purchases=Person.NOTIFY_DAILY)
        organization = OrganizationFactory()
        OrganizationMember.objects.create(
            person=owner,
            organization=organization,
            role=OrganizationMember.OWNER,
        )
        event = EventFactory(organization=organization)
        TransactionFactory(event=event, transaction_type=Transaction.PURCHASE)
        self.assertEqual(len(mail.outbox), 0)
        self.command.send_digest(owner)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, '[Dancerfly] New purchases for your events!')
        self.assertIn(event.name, mail.outbox[0].body)
        self.assertIn(event.name, mail.outbox[0].alternatives[0][0])

    def test_send_digest__owner__no_transactions(self):
        owner = PersonFactory(notify_new_purchases=Person.NOTIFY_DAILY)
        organization = OrganizationFactory()
        OrganizationMember.objects.create(
            person=owner,
            organization=organization,
            role=OrganizationMember.OWNER,
        )
        event = EventFactory(organization=organization)
        TransactionFactory(event=event, transaction_type=Transaction.PURCHASE)
        self.assertEqual(len(mail.outbox), 0)
        self.command.send_digest(owner)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, '[Dancerfly] New purchases for your events!')
        self.assertIn(event.name, mail.outbox[0].body)
        self.assertIn(event.name, mail.outbox[0].alternatives[0][0])

    def test_send_digest__owner__transactions_older_than_one_day(self):
        owner = PersonFactory(notify_new_purchases=Person.NOTIFY_DAILY)
        organization = OrganizationFactory()
        OrganizationMember.objects.create(
            person=owner,
            organization=organization,
            role=OrganizationMember.OWNER,
        )
        event = EventFactory(organization=organization)
        TransactionFactory(
            event=event,
            transaction_type=Transaction.PURCHASE,
            timestamp=timezone.now() - timedelta(days=2),
        )
        self.assertEqual(len(mail.outbox), 0)
        self.command.send_digest(owner)
        self.assertEqual(len(mail.outbox), 0)

    def test_send_digest__owner__transactions_older_than_last_sent(self):
        owner = PersonFactory(
            notify_new_purchases=Person.NOTIFY_DAILY,
            last_new_purchases_digest_sent=timezone.now() - timedelta(hours=1),
        )
        organization = OrganizationFactory()
        OrganizationMember.objects.create(
            person=owner,
            organization=organization,
            role=OrganizationMember.OWNER,
        )
        event = EventFactory(organization=organization)
        TransactionFactory(
            event=event,
            transaction_type=Transaction.PURCHASE,
            timestamp=timezone.now() - timedelta(hours=2),
        )
        self.assertEqual(len(mail.outbox), 0)
        self.command.send_digest(owner)
        self.assertEqual(len(mail.outbox), 0)

    def test_send_digest__owner__two_events(self):
        owner = PersonFactory(notify_new_purchases=Person.NOTIFY_DAILY)
        organization = OrganizationFactory()
        OrganizationMember.objects.create(
            person=owner,
            organization=organization,
            role=OrganizationMember.OWNER,
        )
        event1 = EventFactory(organization=organization)
        event2 = EventFactory(organization=organization)
        TransactionFactory(event=event1, transaction_type=Transaction.PURCHASE)
        TransactionFactory(event=event2, transaction_type=Transaction.PURCHASE)
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
        OrganizationMember.objects.create(
            person=editor,
            organization=event.organization,
            role=OrganizationMember.EDIT,
        )
        TransactionFactory(event=event, transaction_type=Transaction.PURCHASE)
        self.assertEqual(len(mail.outbox), 0)
        self.command.send_digest(editor)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, '[Dancerfly] New purchases for your events!')
        self.assertIn(event.name, mail.outbox[0].body)
        self.assertIn(event.name, mail.outbox[0].alternatives[0][0])

    def test_send_digest__event_editor(self):
        editor = PersonFactory(notify_new_purchases=Person.NOTIFY_DAILY)
        event = EventFactory()
        EventMember.objects.create(
            person=editor,
            event=event,
            role=EventMember.EDIT,
        )
        TransactionFactory(event=event, transaction_type=Transaction.PURCHASE)
        self.assertEqual(len(mail.outbox), 0)
        self.command.send_digest(editor)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, '[Dancerfly] New purchases for your events!')
        self.assertIn(event.name, mail.outbox[0].body)
        self.assertIn(event.name, mail.outbox[0].alternatives[0][0])

    def test_full_send_and_timestamp(self):
        owner = PersonFactory(notify_new_purchases=Person.NOTIFY_DAILY)
        editor = PersonFactory(notify_new_purchases=Person.NOTIFY_DAILY)
        organization = OrganizationFactory()
        OrganizationMember.objects.create(
            person=owner,
            organization=organization,
            role=OrganizationMember.OWNER,
        )
        OrganizationMember.objects.create(
            person=editor,
            organization=organization,
            role=OrganizationMember.EDIT,
        )
        event = EventFactory(organization=organization)
        TransactionFactory(event=event, transaction_type=Transaction.PURCHASE)
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
        organization = OrganizationFactory()
        OrganizationMember.objects.create(
            person=owner,
            organization=organization,
            role=OrganizationMember.OWNER,
        )
        OrganizationMember.objects.create(
            person=editor,
            organization=organization,
            role=OrganizationMember.EDIT,
        )
        event = EventFactory(organization=organization)
        TransactionFactory(event=event, transaction_type=Transaction.PURCHASE)
        self.assertEqual(len(mail.outbox), 0)
        self.command.handle()
        # stderr.write called four times: message & traceback per error.
        self.assertEqual(self.command.stderr.write.call_count, 4)
        self.assertEqual(len(mail.outbox), 0)
