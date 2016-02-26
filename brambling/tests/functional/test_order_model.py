from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import TestCase, RequestFactory

from brambling.models import Order, Transaction
from brambling.tests.factories import (
    EventFactory,
    OrderFactory,
    DiscountFactory,
    ItemFactory,
    ItemOptionFactory,
    PersonFactory,
    TransactionFactory,
)


class OrderModelTestCase(TestCase):
    def test_summary_data__base(self):
        """
        Test that get_summary_data returns correct values for savings and
        total cost.

        """
        event = EventFactory()
        order = OrderFactory(event=event)
        transaction = TransactionFactory(event=event, order=order)
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)
        discount = DiscountFactory(amount=20, event=event, item_options=[item_option])

        order.add_to_cart(item_option)
        order.mark_cart_paid(transaction)

        summary_data = order.get_summary_data()
        self.assertEqual(summary_data['gross_cost'], 100)
        self.assertEqual(summary_data['total_savings'], 0)
        self.assertEqual(summary_data['net_cost'], 100)

        # Discounts don't get added to BOUGHT items.
        order.add_discount(discount)

        summary_data = order.get_summary_data()
        self.assertEqual(summary_data['gross_cost'], 100)
        self.assertEqual(summary_data['total_savings'], 0)
        self.assertEqual(summary_data['net_cost'], 100)

    def test_summary_data__discount(self):
        """
        Test that get_summary_data returns correct values for savings and
        total cost.

        """
        event = EventFactory()
        order = OrderFactory(event=event)
        transaction = TransactionFactory(event=event, order=order)
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)
        discount = DiscountFactory(amount=20, event=event, item_options=[item_option])

        order.add_to_cart(item_option)
        order.add_discount(discount)
        order.mark_cart_paid(transaction)

        summary_data = order.get_summary_data()
        self.assertEqual(summary_data['gross_cost'], 100)
        self.assertEqual(summary_data['total_savings'], -20)
        self.assertEqual(summary_data['net_cost'], 80)

    def test_summary_data__itemoption_changed(self):
        """
        Test that get_summary_data returns correct values for savings and
        total cost even if an itemoption was changed.

        """
        event = EventFactory()
        order = OrderFactory(event=event)
        transaction = TransactionFactory(event=event, order=order)
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)

        order.add_to_cart(item_option)
        order.mark_cart_paid(transaction)

        summary_data = order.get_summary_data()
        self.assertEqual(summary_data['gross_cost'], 100)
        self.assertEqual(summary_data['total_savings'], 0)
        self.assertEqual(summary_data['net_cost'], 100)

        item_option.price = 200
        item_option.save()

        # Make sure that the value isn't cached.
        order = Order.objects.get(pk=order.pk)

        summary_data = order.get_summary_data()
        self.assertEqual(summary_data['gross_cost'], 100)
        self.assertEqual(summary_data['total_savings'], 0)
        self.assertEqual(summary_data['net_cost'], 100)

    def test_summary_data__itemoption_changed__discount(self):
        """
        Test that get_summary_data returns correct values for savings and
        total cost even if an itemoption was changed.

        """
        event = EventFactory()
        order = OrderFactory(event=event)
        transaction = TransactionFactory(event=event, order=order)
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)
        discount = DiscountFactory(amount=20, event=event, item_options=[item_option])

        order.add_to_cart(item_option)
        order.add_discount(discount)
        order.mark_cart_paid(transaction)

        summary_data = order.get_summary_data()
        self.assertEqual(summary_data['gross_cost'], 100)
        self.assertEqual(summary_data['total_savings'], -20)
        self.assertEqual(summary_data['net_cost'], 80)

        item_option.price = 200
        item_option.save()

        # Make sure that the value isn't cached.
        order = Order.objects.get(pk=order.pk)

        summary_data = order.get_summary_data()
        self.assertEqual(summary_data['gross_cost'], 100)
        self.assertEqual(summary_data['total_savings'], -20)
        self.assertEqual(summary_data['net_cost'], 80)

    def test_summary_data__itemoption_deleted(self):
        """
        Test that get_summary_data returns correct values for savings and
        total cost even if an itemoption was deleted.

        """
        event = EventFactory()
        order = OrderFactory(event=event)
        transaction = TransactionFactory(event=event, order=order)
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)

        order.add_to_cart(item_option)
        order.mark_cart_paid(transaction)

        summary_data = order.get_summary_data()
        self.assertEqual(summary_data['gross_cost'], 100)
        self.assertEqual(summary_data['total_savings'], 0)
        self.assertEqual(summary_data['net_cost'], 100)

        item_option.delete()

        # Make sure that the value isn't cached.
        order = Order.objects.get(pk=order.pk)

        summary_data = order.get_summary_data()
        self.assertEqual(summary_data['gross_cost'], 100)
        self.assertEqual(summary_data['total_savings'], 0)
        self.assertEqual(summary_data['net_cost'], 100)

    def test_summary_data__itemoption_deleted__discount(self):
        """
        Test that get_summary_data returns correct values for savings and
        total cost even if an itemoption was deleted.

        """
        event = EventFactory()
        order = OrderFactory(event=event)
        transaction = TransactionFactory(event=event, order=order)
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)
        discount = DiscountFactory(amount=20, event=event, item_options=[item_option])

        order.add_to_cart(item_option)
        order.add_discount(discount)
        order.mark_cart_paid(transaction)

        summary_data = order.get_summary_data()
        self.assertEqual(summary_data['gross_cost'], 100)
        self.assertEqual(summary_data['total_savings'], -20)
        self.assertEqual(summary_data['net_cost'], 80)

        item_option.delete()

        # Make sure that the value isn't cached.
        order = Order.objects.get(pk=order.pk)

        summary_data = order.get_summary_data()
        self.assertEqual(summary_data['gross_cost'], 100)
        self.assertEqual(summary_data['total_savings'], -20)
        self.assertEqual(summary_data['net_cost'], 80)

    def test_summary_data__discount_changed(self):
        """
        Test that get_summary_data returns correct values for savings and
        total cost even if a discount was changed.

        """
        event = EventFactory()
        order = OrderFactory(event=event)
        transaction = TransactionFactory(event=event, order=order)
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)
        discount = DiscountFactory(amount=20, event=event, item_options=[item_option])

        order.add_to_cart(item_option)
        order.add_discount(discount)
        order.mark_cart_paid(transaction)

        summary_data = order.get_summary_data()
        self.assertEqual(summary_data['gross_cost'], 100)
        self.assertEqual(summary_data['total_savings'], -20)
        self.assertEqual(summary_data['net_cost'], 80)

        discount.amount = 100
        discount.save()

        # Make sure that the value isn't cached.
        order = Order.objects.get(pk=order.pk)

        summary_data = order.get_summary_data()
        self.assertEqual(summary_data['gross_cost'], 100)
        self.assertEqual(summary_data['total_savings'], -20)
        self.assertEqual(summary_data['net_cost'], 80)

    def test_summary_data__discount_deleted(self):
        """
        Test that get_summary_data returns correct values for savings and
        total cost even if a discount was deleted.

        """
        event = EventFactory()
        order = OrderFactory(event=event)
        transaction = TransactionFactory(event=event, order=order)
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)
        discount = DiscountFactory(amount=20, event=event, item_options=[item_option])

        order.add_to_cart(item_option)
        order.add_discount(discount)
        order.mark_cart_paid(transaction)

        summary_data = order.get_summary_data()
        self.assertEqual(summary_data['gross_cost'], 100)
        self.assertEqual(summary_data['total_savings'], -20)
        self.assertEqual(summary_data['net_cost'], 80)

        discount.delete()

        # Make sure that the value isn't cached.
        order = Order.objects.get(pk=order.pk)

        summary_data = order.get_summary_data()
        self.assertEqual(summary_data['gross_cost'], 100)
        self.assertEqual(summary_data['total_savings'], -20)
        self.assertEqual(summary_data['net_cost'], 80)

    def test_summary_data__transaction_no_items(self):
        """
        Transactions without items are included in summary data.

        """
        event = EventFactory()
        order = OrderFactory(event=event)
        TransactionFactory(event=event, order=order, amount=100)

        summary_data = order.get_summary_data()
        self.assertEqual(summary_data['total_payments'], 100)
        self.assertEqual(summary_data['total_refunds'], 0)
        self.assertEqual(summary_data['net_balance'], -100)

        TransactionFactory(
            event=event,
            order=order,
            amount=-100,
            transaction_type=Transaction.REFUND
        )
        summary_data = order.get_summary_data()
        self.assertEqual(summary_data['total_payments'], 100)
        self.assertEqual(summary_data['total_refunds'], -100)
        self.assertEqual(summary_data['net_balance'], 0)

    def test_summary_data__items_no_transaction(self):
        """
        Items without transactions are included in summary data.

        """
        event = EventFactory()
        order = OrderFactory(event=event)
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)

        order.add_to_cart(item_option)
        summary_data = order.get_summary_data()
        self.assertEqual(summary_data['gross_cost'], 100)
        self.assertEqual(summary_data['total_savings'], 0)
        self.assertEqual(summary_data['net_cost'], 100)

    def test_summary_data__items_no_transaction__discount(self):
        """
        Items without transactions are included in summary data.

        """
        event = EventFactory()
        order = OrderFactory(event=event)
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)
        discount = DiscountFactory(amount=20, event=event, item_options=[item_option])

        order.add_to_cart(item_option)
        order.add_discount(discount)
        summary_data = order.get_summary_data()
        self.assertEqual(summary_data['gross_cost'], 100)
        self.assertEqual(summary_data['total_savings'], -20)
        self.assertEqual(summary_data['net_cost'], 80)

    def test_cart_boughtitem_caching(self):
        """
        Test that the cached boughtitem information is correct.
        """
        event = EventFactory()
        order = OrderFactory(event=event)
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)

        order.add_to_cart(item_option)

        item.delete()

        self.assertTrue(order.bought_items.exists())
        boughtitem = order.bought_items.all()[0]
        self.assertTrue(boughtitem.item_option_id is None)
        self.assertEqual(boughtitem.item_name, item.name)
        self.assertEqual(boughtitem.item_description, item.description)
        self.assertEqual(boughtitem.item_option_name, item_option.name)
        self.assertEqual(boughtitem.price, item_option.price)
        self.assertTrue(boughtitem.item_option_id is None)

    def test_cart_discount_caching(self):
        """
        Test that the cached discount information is correct.
        """
        event = EventFactory()
        order = OrderFactory(event=event)
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)
        discount = DiscountFactory(amount=20, event=event, item_options=[item_option])

        order.add_to_cart(item_option)
        order.add_discount(discount)

        discount.delete()

        self.assertTrue(order.bought_items.exists())
        boughtitem = order.bought_items.all()[0]
        self.assertTrue(boughtitem.discounts.exists())
        boughtitemdiscount = boughtitem.discounts.all()[0]

        self.assertTrue(boughtitemdiscount.discount_id is None)
        self.assertEqual(boughtitemdiscount.name, discount.name)
        self.assertEqual(boughtitemdiscount.code, discount.code)
        self.assertEqual(boughtitemdiscount.discount_type, discount.discount_type)
        self.assertEqual(boughtitemdiscount.amount, discount.amount)

        self.assertEqual(boughtitemdiscount.savings(), 20)


class OrderManagerTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.session_middleware = SessionMiddleware()

    def _add_session(self, request):
        self.session_middleware.process_request(request)

    def test_for_request__code__anon_anon(self):
        """Anonymous users forbidden to access anonymous orders."""
        event = EventFactory()
        OrderFactory(event=event, person=None)
        request = self.factory.get('/')
        self._add_session(request)
        request.user = AnonymousUser()
        with self.assertRaises(Order.DoesNotExist):
            Order.objects.for_request(event, request, create=False)

    def test_for_request__code__authed_anon(self):
        """Authenticated users cannot access orders created by anonymous users
        without the code stored in the session.
        """
        event = EventFactory()
        person = PersonFactory()
        OrderFactory(event=event, person=None)
        request = self.factory.get('/')
        self._add_session(request)
        request.user = person
        with self.assertRaises(Order.DoesNotExist):
            Order.objects.for_request(event, request, create=False)

    def test_for_request__code__anon_authed(self):
        """An anonymous user can't access an order created by an authenticated
        user.
        """
        event = EventFactory()
        person = PersonFactory()
        order = OrderFactory(event=event, person=person)
        request = self.factory.get('/')
        self._add_session(request)
        Order.objects._set_session_code(request, event, order.code)
        request.user = AnonymousUser()
        with self.assertRaises(Order.DoesNotExist):
            Order.objects.for_request(event, request, create=False)

    def test_for_request__code__authed_other_authed(self):
        """An authenticated user can't access orders created by anyone else."""
        event = EventFactory()
        person = PersonFactory()
        person2 = PersonFactory()
        order = OrderFactory(event=event, person=person2)
        request = self.factory.get('/')
        self._add_session(request)
        Order.objects._set_session_code(request, event, order.code)
        request.user = person
        with self.assertRaises(Order.DoesNotExist):
            Order.objects.for_request(event, request, create=False)

    def test_for_request__authed(self):
        """An authenticated user will automatically get their own order."""
        event = EventFactory()
        person = PersonFactory()
        order = OrderFactory(event=event, person=person)
        request = self.factory.get('/')
        request.user = person
        fetched, created = Order.objects.for_request(event, request,
                                                     create=False)
        self.assertFalse(created)
        self.assertEqual(fetched, order)

    def test_for_request__session__anon_anon(self):
        """An anonymous user can have their order stored in the session."""
        event = EventFactory()
        order = OrderFactory(event=event, person=None)
        request = self.factory.get('/')
        self._add_session(request)
        Order.objects._set_session_code(request, event, order.code)
        request.user = AnonymousUser()

        fetched, created = Order.objects.for_request(event, request,
                                                     create=False)
        self.assertFalse(created)
        self.assertEqual(fetched, order)

    def test_for_request__session__authed_anon(self):
        """
        An authenticated user can auto-claim a session-stored order.
        """
        event = EventFactory()
        person = PersonFactory()
        order = OrderFactory(event=event, person=None)
        request = self.factory.get('/')
        self._add_session(request)
        Order.objects._set_session_code(request, event, order.code)
        request.user = person

        fetched, created = Order.objects.for_request(event, request,
                                                     create=False)
        self.assertFalse(created)
        self.assertEqual(fetched, order)
        self.assertEqual(fetched.person_id, person.id)

    def test_for_request__session__authed_anon__with_order(self):
        """
        An authenticated user's own order will take precedence over
        a session order.
        """
        event = EventFactory()
        person = PersonFactory()
        order = OrderFactory(event=event, person=None)
        order2 = OrderFactory(event=event, person=person)
        request = self.factory.get('/')
        self._add_session(request)
        Order.objects._set_session_code(request, event, order.code)
        request.user = person

        fetched, created = Order.objects.for_request(event, request,
                                                     create=False)
        self.assertFalse(created)
        self.assertEqual(fetched, order2)

    def test_for_request__create__anon(self):
        """
        An anonymous user will get a new order back if no code is provided
        and no session code is available, but create is True.
        """
        event = EventFactory()
        request = self.factory.get('/')
        request.user = AnonymousUser()
        self._add_session(request)
        fetched, created = Order.objects.for_request(event, request, create=True)
        self.assertTrue(created)
        self.assertEqual(fetched.code, Order.objects._get_session_code(request, event))
        self.assertIsNone(fetched.person)

    def test_for_request__create__authed(self):
        """
        An authenticated user will get a new order back if no code is provided
        and no session code is available, but create is True.
        """
        event = EventFactory()
        person = PersonFactory()
        request = self.factory.get('/')
        request.user = person
        self._add_session(request)
        fetched, created = Order.objects.for_request(event, request, create=True)
        self.assertTrue(created)
        self.assertIsNone(Order.objects._get_session_code(request, event))
        self.assertEqual(fetched.person_id, person.id)
