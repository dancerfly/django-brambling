# encoding: utf-8
from django.test import TestCase, RequestFactory

from brambling.api.v1.views import (
    AttendeeViewSet, BoughtItemViewSet, ItemOptionViewSet
)
from brambling.models import (
    Transaction,
    BoughtItem,
    EventMember,
)
from brambling.tests.factories import (
    DiscountFactory,
    EventFactory,
    OrderFactory,
    AttendeeFactory,
    PersonFactory,
    ItemFactory,
    ItemOptionFactory,
    TransactionFactory,
)


class AttendeeViewSetTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_queryset_distinct(self):
        """
        For authenticated users, make sure the qs is distinct.
        Specifically, having multiple additional editors on
        the event shouldn't cause duplication issues.
        """
        person = PersonFactory()
        editor1 = PersonFactory()
        editor2 = PersonFactory()
        editor3 = PersonFactory()
        event = EventFactory(collect_housing_data=False)
        EventMember.objects.create(
            person=editor1,
            event=event,
            role=EventMember.EDIT,
        )
        EventMember.objects.create(
            person=editor2,
            event=event,
            role=EventMember.EDIT,
        )
        EventMember.objects.create(
            person=editor3,
            event=event,
            role=EventMember.EDIT,
        )
        order = OrderFactory(event=event, person=person)
        att1 = AttendeeFactory(order=order)
        att2 = AttendeeFactory(order=order)
        att3 = AttendeeFactory(order=order)

        viewset = AttendeeViewSet()
        viewset.request = self.factory.get('/')
        viewset.request.user = person

        qs = viewset.get_queryset()
        self.assertEqual(len(qs), 3)
        self.assertEqual(set(qs), set((att1, att2, att3)))


class BoughtItemViewSetTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_queryset_distinct(self):
        """
        For authenticated users, make sure the qs is distinct.
        Specifically, having multiple additional editors on
        the event shouldn't cause duplication issues.
        """
        person = PersonFactory()
        editor1 = PersonFactory()
        editor2 = PersonFactory()
        editor3 = PersonFactory()
        event = EventFactory(collect_housing_data=False)
        EventMember.objects.create(
            person=editor1,
            event=event,
            role=EventMember.EDIT,
        )
        EventMember.objects.create(
            person=editor2,
            event=event,
            role=EventMember.EDIT,
        )
        EventMember.objects.create(
            person=editor3,
            event=event,
            role=EventMember.EDIT,
        )
        order = OrderFactory(event=event, person=person)
        att1 = AttendeeFactory(order=order)
        att2 = AttendeeFactory(order=order)
        att3 = AttendeeFactory(order=order)

        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)

        order.add_to_cart(item_option)
        order.add_to_cart(item_option)

        viewset = BoughtItemViewSet()
        viewset.request = self.factory.get('/')
        viewset.request.user = person

        qs = viewset.get_queryset()
        self.assertEqual(len(qs), 2)
        self.assertEqual(set(qs), set(order.bought_items.all()))


class ItemOptionViewSetTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        event = EventFactory()
        self.order = OrderFactory(event=event, email='cicero@example.com')
        self.transaction = TransactionFactory(
            event=event, order=self.order, amount=130,
            method=Transaction.CHECK, is_confirmed=False)
        item = ItemFactory(event=event, name='Multipass')
        item_option1 = ItemOptionFactory(price=100, item=item, name='Gold')
        item_option2 = ItemOptionFactory(price=60, item=item, name='Silver')

        discount = DiscountFactory(amount=30, discount_type='percent',
                                   event=event, item_options=[item_option1])

        self.order.add_to_cart(item_option1)
        self.order.add_to_cart(item_option2)
        self.order.add_discount(discount)
        self.order.mark_cart_paid(self.transaction)

        order2 = OrderFactory(event=event, email='caesar@example.com')
        order2.add_to_cart(item_option2)
        transaction2 = TransactionFactory(event=event, order=self.order,
                                         amount=130, method=Transaction.CHECK,
                                         is_confirmed=True)
        order2.mark_cart_paid(transaction2)


        self.order3 = OrderFactory(event=event, email='caesar@example.com')
        self.order3.add_to_cart(item_option1)
        transaction3 = TransactionFactory(event=event, order=self.order3,
                                         amount=130, method=Transaction.CHECK,
                                         is_confirmed=True)
        self.order3.mark_cart_paid(transaction3)

        self.viewset = ItemOptionViewSet()
        self.viewset.request = self.factory.get('/')
        self.viewset.request.user = self.order.person

    def test_taken_counts(self):
        qs = self.viewset.get_queryset()
        self.assertEqual([2, 2], [int(p.taken) for p in qs])

    def test_exclude_refunded(self):
        """should exclude refunded items from the taken count"""
        self.transaction.refund()
        qs = self.viewset.get_queryset()
        self.assertEqual([1, 1], [int(p.taken) for p in qs])

    def test_exclude_transferred(self):
        """should exclude transferred items from the taken count"""
        for item in self.order3.bought_items.all():
            item.status = BoughtItem.TRANSFERRED
            item.save()
        qs = self.viewset.get_queryset()
        self.assertEqual([1, 2], [int(p.taken) for p in qs])
