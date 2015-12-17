from django.test import TestCase

from zenaida.templatetags.zenaida import format_money

from brambling.mail import OrderReceiptMailer
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

        self.mailer = OrderReceiptMailer(transaction, site='dancerfly.com',
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
        self.assertIn(self.discount_amount, body)
        self.assertIn(self.item_price, body)
        self.assertIn(self.option1, body)
        self.assertIn(self.option2, body)

    def test_render_inlined(self):
        body = self.mailer.render_body(self.mailer.get_context_data(),
                                       inlined=True)
        self.assertIn(self.option1, body)
        self.assertIn(self.option2, body)
        self.assertIn(self.item_price, body)
        self.assertIn(self.discount_amount, body)
        self.assertIn(self.total_amount, body)

    def test_recipients(self):
        self.assertEqual(self.mailer.get_recipients(), [self.person.email])

    def test_subject(self):
        subject = self.mailer.render_subject(self.mailer.get_context_data())
        expected_subject = ('[{event_name}] Receipt for order {order_code}'
                            .format(event_name=self.event_name,
                                    order_code=self.order.code))
        self.assertEqual(subject, expected_subject)

    def test_body_non_inlined_non_plaintext(self):
        body = self.mailer.render_body(self.mailer.get_context_data(),
                                       inlined=False, plaintext=False)
        self.assertIn(self.option1, body)
        self.assertIn(self.option2, body)
        self.assertIn(self.item_price, body)
        self.assertIn(self.discount_amount, body)
        self.assertIn(self.total_amount, body)


class OrderReceiptMailerForNonUserTestCase(TestCase):

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

        self.mailer = OrderReceiptMailer(transaction, site='dancerfly.com',
                                         secure=True)

    def test_recipients(self):
        self.assertEqual(self.mailer.get_recipients(), [self.order.email])
