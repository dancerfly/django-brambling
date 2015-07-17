from django.test import TestCase

from brambling.models import Order
from brambling.tests.factories import (EventFactory, OrderFactory, DiscountFactory, ItemFactory, ItemOptionFactory)


class OrderModelTestCase(TestCase):
    def test_summary_data__base(self):
        """
        Test that get_summary_data returns correct values for savings and
        total cost.

        """
        event = EventFactory()
        order = OrderFactory(event=event)
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)
        discount = DiscountFactory(amount=20, event=event, item_options=[item_option])

        order.add_to_cart(item_option)

        summary_data = order.get_summary_data()
        self.assertEqual(summary_data['gross_cost'], 100)
        self.assertEqual(summary_data['total_savings'], 0)
        self.assertEqual(summary_data['net_cost'], 100)

        order.add_discount(discount)

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
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)
        discount = DiscountFactory(amount=20, event=event, item_options=[item_option])

        order.add_to_cart(item_option)

        summary_data = order.get_summary_data()
        self.assertEqual(summary_data['gross_cost'], 100)
        self.assertEqual(summary_data['total_savings'], 0)
        self.assertEqual(summary_data['net_cost'], 100)

        order.add_discount(discount)

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
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)
        discount = DiscountFactory(amount=20, event=event, item_options=[item_option])

        order.add_to_cart(item_option)

        summary_data = order.get_summary_data()
        self.assertEqual(summary_data['gross_cost'], 100)
        self.assertEqual(summary_data['total_savings'], 0)
        self.assertEqual(summary_data['net_cost'], 100)

        order.add_discount(discount)

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
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)
        discount = DiscountFactory(amount=20, event=event, item_options=[item_option])

        order.add_to_cart(item_option)

        summary_data = order.get_summary_data()
        self.assertEqual(summary_data['gross_cost'], 100)
        self.assertEqual(summary_data['total_savings'], 0)
        self.assertEqual(summary_data['net_cost'], 100)

        order.add_discount(discount)

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
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)
        discount = DiscountFactory(amount=20, event=event, item_options=[item_option])

        order.add_to_cart(item_option)

        summary_data = order.get_summary_data()
        self.assertEqual(summary_data['gross_cost'], 100)
        self.assertEqual(summary_data['total_savings'], 0)
        self.assertEqual(summary_data['net_cost'], 100)

        order.add_discount(discount)

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
