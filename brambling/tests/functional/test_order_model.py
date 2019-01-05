from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import TestCase, RequestFactory
from mock import Mock

from brambling.models import (
    BoughtItemDiscount,
    Order,
    Transaction,
)
from brambling.tests.factories import (
    EventFactory,
    OrderFactory,
    DiscountFactory,
    ItemFactory,
    ItemOptionFactory,
    PersonFactory,
    TransactionFactory,
)
from brambling.utils.invites import TransferInvite


class AddDiscountTestCase(TestCase):
    def setUp(self):
        self.event = EventFactory()
        self.order = OrderFactory(event=self.event)
        self.item = ItemFactory(event=self.event)
        self.item_option = ItemOptionFactory(price=100, item=self.item)
        self.order.add_to_cart(self.item_option)
        self.discount = DiscountFactory(amount=20, event=self.event, item_options=[self.item_option])

    def test_add_discount_creates_boughtitemdiscount(self):
        created = self.order.add_discount(self.discount)
        self.assertTrue(created)
        bought_item = self.order.bought_items.get()
        self.assertEqual(bought_item.discounts.count(), 1)
        bought_item_discount = bought_item.discounts.get()
        self.assertEqual(bought_item_discount.discount, self.discount)

    def test_add_discount_does_not_duplicate_discounts(self):
        existing_bought_item_discount = BoughtItemDiscount.objects.create(
            discount=self.discount,
            bought_item=self.order.bought_items.get(),
            name=self.discount.name,
            code=self.discount.code,
            discount_type=self.discount.discount_type,
            amount=self.discount.amount,
        )

        created = self.order.add_discount(self.discount)
        self.assertFalse(created)
        bought_item = self.order.bought_items.get()
        self.assertEqual(bought_item.discounts.count(), 1)
        bought_item_discount = bought_item.discounts.get()
        self.assertEqual(bought_item_discount, existing_bought_item_discount)

    def test_created_true_if_any_discounts_created(self):
        item_option2 = ItemOptionFactory(price=100, item=self.item)
        self.discount.item_options.add(item_option2)
        BoughtItemDiscount.objects.create(
            discount=self.discount,
            bought_item=self.order.bought_items.get(),
            name=self.discount.name,
            code=self.discount.code,
            discount_type=self.discount.discount_type,
            amount=self.discount.amount,
        )

        created = self.order.add_discount(self.discount)
        self.assertTrue(created)
        bought_item = self.order.bought_items.get(item_option=item_option2)
        self.assertEqual(bought_item.discounts.count(), 1)
        bought_item_discount = bought_item.discounts.get()
        self.assertEqual(bought_item_discount.discount, self.discount)


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

    def test_summary_data__transfer(self):
        """Items sent or received in a transfer shouldn't count towards net cost and savings"""
        event = EventFactory()
        order = OrderFactory(
            event=event,
            person=PersonFactory(),
        )
        person2 = PersonFactory()
        transaction = TransactionFactory(
            event=event,
            order=order,
            is_confirmed=True,
            transaction_type=Transaction.PURCHASE,
            amount=80,
        )
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)
        discount = DiscountFactory(amount=20, event=event, item_options=[item_option])

        order.add_to_cart(item_option)
        order.add_discount(discount)
        order.mark_cart_paid(transaction)

        bought_item = transaction.bought_items.get()
        invite = TransferInvite.get_or_create(
            request=Mock(user=person2, session={}),
            email=person2.email,
            content=bought_item,
        )[0]
        invite.accept()

        summary_data = order.get_summary_data()
        self.assertEqual(summary_data['gross_cost'], 100)
        self.assertEqual(summary_data['total_savings'], -20)
        self.assertEqual(summary_data['total_refunds'], 0)
        self.assertEqual(summary_data['total_payments'], 80)
        self.assertEqual(summary_data['net_cost'], 80)
        self.assertEqual(summary_data['net_balance'], 0)
        self.assertEqual(summary_data['unconfirmed_check_payments'], False)
        transactions = summary_data['transactions']
        self.assertEqual(len(transactions), 2)
        transfer_txn, transfer_txn_dict = transactions.items()[0]
        self.assertEqual(transfer_txn.transaction_type, Transaction.TRANSFER)
        self.assertEqual(transfer_txn_dict['items'], [bought_item])
        self.assertEqual(transfer_txn_dict['gross_cost'], 0)
        self.assertEqual(transfer_txn_dict['discounts'], [])
        self.assertEqual(transfer_txn_dict['total_savings'], 0)
        self.assertEqual(transfer_txn_dict['net_cost'], 0)
        purchase_txn, purchase_txn_dict = transactions.items()[1]
        self.assertEqual(purchase_txn.transaction_type, Transaction.PURCHASE)
        self.assertEqual(purchase_txn_dict['items'], [bought_item])
        self.assertEqual(purchase_txn_dict['gross_cost'], 100)
        self.assertEqual(purchase_txn_dict['discounts'], [bought_item.discounts.first()])
        self.assertEqual(purchase_txn_dict['total_savings'], -20)
        self.assertEqual(purchase_txn_dict['net_cost'], 80)

        order2 = Order.objects.get(event=event, person=person2)
        summary_data2 = order2.get_summary_data()
        self.assertEqual(summary_data2['gross_cost'], 0)
        self.assertEqual(summary_data2['total_savings'], 0)
        self.assertEqual(summary_data2['total_refunds'], 0)
        self.assertEqual(summary_data2['total_payments'], 0)
        self.assertEqual(summary_data2['net_cost'], 0)
        self.assertEqual(summary_data2['net_balance'], 0)
        self.assertEqual(summary_data2['unconfirmed_check_payments'], False)
        transactions2 = summary_data2['transactions']
        self.assertEqual(len(transactions2), 1)
        transfer_txn2, transfer_txn2_dict = transactions.items()[0]
        self.assertEqual(transfer_txn2.transaction_type, Transaction.TRANSFER)
        self.assertEqual(transfer_txn2_dict['items'], [bought_item])
        self.assertEqual(transfer_txn2_dict['gross_cost'], 0)
        self.assertEqual(transfer_txn2_dict['discounts'], [])
        self.assertEqual(transfer_txn2_dict['total_savings'], 0)
        self.assertEqual(transfer_txn2_dict['net_cost'], 0)

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
