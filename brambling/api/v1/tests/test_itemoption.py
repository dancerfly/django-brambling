# encoding: utf-8
from django.test import TestCase, RequestFactory

from brambling.api.v1.endpoints.itemoption import ItemOptionViewSet
from brambling.models import (
    Transaction,
    BoughtItem,
)
from brambling.tests.factories import (
    DiscountFactory,
    EventFactory,
    ItemFactory,
    ItemOptionFactory,
    OrderFactory,
    TransactionFactory,
)


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
