from django.test import TestCase

from zenaida.templatetags.zenaida import format_money

from brambling.mail import OrderAlertMailer
from brambling.models import Transaction
from brambling.tests.factories import (EventFactory, OrderFactory,
                                       TransactionFactory, ItemFactory,
                                       ItemOptionFactory, AttendeeFactory,
                                       DiscountFactory, PersonFactory)


class OrderReceiptMailerTestCase(TestCase):

    def setUp(self):
        self.person = PersonFactory()
        event = EventFactory()
        self.order = OrderFactory(event=event, person=self.person)
        transaction = TransactionFactory(event=event, order=self.order,
                                         amount=130)
        item = ItemFactory(event=event, name='Multipass')
        item_option1 = ItemOptionFactory(price=100, item=item, name='Gold')
        item_option2 = ItemOptionFactory(price=60, item=item, name='Silver')

        discount = DiscountFactory(amount=30, discount_type='percent',
                                   event=event, item_options=[item_option1])

        self.order.add_to_cart(item_option1)
        self.order.add_to_cart(item_option2)
        self.order.add_discount(discount)
        self.order.mark_cart_paid(transaction)

        self.mailer = OrderAlertMailer(transaction, site='dancerfly.com',
                                       secure=True)
        self.event_name = event.name
        self.discount_amount = format_money(discount.amount, event.currency)
        self.total_amount = format_money(transaction.amount, event.currency)
        self.option1 = '{0} ({1})'.format(item.name, item_option1.name)
        self.option2 = '{0} ({1})'.format(item.name, item_option1.name)
        self.item_price = format_money(item_option1.price, event.currency)

    def test_render_plaintext(self):
        body = self.mailer.render_body(self.mailer.get_context_data(),
                                       plaintext=True)
        self.assertIn(self.total_amount, body)
        self.assertIn(self.option1, body)
        self.assertIn(self.option2, body)
        self.assertNotIn("outstanding check payments", body)

    def test_render_inlined(self):
        body = self.mailer.render_body(self.mailer.get_context_data(),
                                       inlined=True)
        self.assertIn(self.option1, body)
        self.assertIn(self.option2, body)
        self.assertIn(self.total_amount, body)

    def test_recipients(self):
        self.assertSequenceEqual(self.mailer.get_recipients(),
                                 [self.order.event.organization.owner.email])

    def test_recipients__notify_never(self):
        person = self.order.event.organization.owner
        person.notify_new_purchases = 'never'
        person.save()
        self.assertSequenceEqual(self.mailer.get_recipients(),
                                 [])

    def test_recipients__notify_daily(self):
        person = self.order.event.organization.owner
        person.notify_new_purchases = 'daily'
        person.save()
        self.assertSequenceEqual(self.mailer.get_recipients(),
                                 [])

    def test_subject(self):
        subject = self.mailer.render_subject(self.mailer.get_context_data())
        expected_subject = ('[{event_name}] New purchase by {person_name}'
                            .format(event_name=self.event_name,
                                    person_name=self.person.get_full_name()))
        self.assertEqual(subject, expected_subject)

    def test_body_non_inlined_non_plaintext(self):
        body = self.mailer.render_body(self.mailer.get_context_data(),
                                       inlined=False, plaintext=False)
        self.assertIn(self.option1, body)
        self.assertIn(self.option2, body)
        self.assertIn(self.total_amount, body)

    def test_subject_apostrophe(self):
        event = EventFactory(name="Han & Leia's Wedding!")
        self.person = PersonFactory(first_name="Ma'ayan", last_name="Plaut")
        self.event_name = event.name
        self.order = OrderFactory(event=event, person=self.person)
        transaction = TransactionFactory(event=event, order=self.order,amount=130)
        self.mailer = OrderAlertMailer(transaction, site='dancerfly.com',
                                       secure=True)
        subject = self.mailer.render_subject(self.mailer.get_context_data())
        expected_subject = ('[{event_name}] New purchase by {person_name}'
                            .format(event_name=self.event_name,
                                    person_name=self.person.get_full_name()))
        self.assertEqual(subject, expected_subject)


class OrderAlertMailerForNonUserOrderTestCase(TestCase):

    def setUp(self):
        event = EventFactory()
        self.order = OrderFactory(event=event, email='cicero@example.com')
        transaction = TransactionFactory(event=event, order=self.order,
                                         amount=130)
        item = ItemFactory(event=event, name='Multipass')
        item_option1 = ItemOptionFactory(price=100, item=item, name='Gold')
        item_option2 = ItemOptionFactory(price=60, item=item, name='Silver')

        discount = DiscountFactory(amount=30, discount_type='percent',
                                   event=event, item_options=[item_option1])

        self.order.add_to_cart(item_option1)
        self.order.add_to_cart(item_option2)
        self.order.add_discount(discount)
        self.order.mark_cart_paid(transaction)

        self.mailer = OrderAlertMailer(transaction, site='dancerfly.com',
                                       secure=True)
        self.event_name = event.name

    def test_subject(self):
        subject = self.mailer.render_subject(self.mailer.get_context_data())
        expected_subject = ('[{event_name}] New purchase by {order_email}'
                            .format(event_name=self.event_name,
                                    order_email=self.order.email))
        self.assertEqual(subject, expected_subject)


class OrderAlertMailerWithUnconfirmedCheckPayments(TestCase):

    def setUp(self):
        event = EventFactory()
        self.order = OrderFactory(event=event, email='cicero@example.com')
        transaction = TransactionFactory(event=event, order=self.order,
                                         amount=130, method=Transaction.CHECK,
                                         is_confirmed=False)
        item = ItemFactory(event=event, name='Multipass')
        item_option1 = ItemOptionFactory(price=100, item=item, name='Gold')
        item_option2 = ItemOptionFactory(price=60, item=item, name='Silver')

        discount = DiscountFactory(amount=30, discount_type='percent',
                                   event=event, item_options=[item_option1])

        self.order.add_to_cart(item_option1)
        self.order.add_to_cart(item_option2)
        self.order.add_discount(discount)
        self.order.mark_cart_paid(transaction)

        self.mailer = OrderAlertMailer(transaction, site='dancerfly.com',
                                       secure=True)
        self.event_name = event.name

    def test_body_plaintext(self):
        body = self.mailer.render_body(self.mailer.get_context_data(),
                                       plaintext=True)
        self.assertIn("keep an eye on your mail", body)
