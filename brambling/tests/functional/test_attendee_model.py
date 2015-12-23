from django.test import TestCase

from brambling.models import Attendee
from brambling.tests.factories import EventFactory, OrderFactory, TransactionFactory, ItemFactory, ItemOptionFactory, AttendeeFactory

class AttendeeModelTestCase(TestCase):

    def test_needs_housing(self):
        event = EventFactory(collect_housing_data=False)
        order = OrderFactory(event=event)
        transaction = TransactionFactory(event=event, order=order)
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)

        order.add_to_cart(item_option)
        order.add_to_cart(item_option)
        order.mark_cart_paid(transaction)

        a1 = AttendeeFactory(order=order, bought_items=order.bought_items.all(),
                            housing_status=Attendee.NEED)
        a2 = AttendeeFactory(order=order, bought_items=order.bought_items.all())
        self.assertTrue(a1.needs_housing())
        self.assertFalse(a2.needs_housing())
