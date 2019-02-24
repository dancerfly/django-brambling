from decimal import Decimal

from django.test import TestCase

from brambling.models import BoughtItem
from brambling.forms.organizer import TransactionRefundForm
from brambling.tests.factories import (
    TransactionFactory, ItemFactory, ItemOptionFactory, EventFactory,
    PersonFactory, OrderFactory
)


class TransactionRefundFormTestCase(TestCase):
    def setUp(self):
        self.person = PersonFactory()
        self.event = EventFactory()
        self.item = ItemFactory(event=self.event, name='Multipass')
        self.order = OrderFactory(event=self.event, person=self.person)
        self.item_option1 = ItemOptionFactory(price=100, item=self.item, name='Gold')
        self.item_option2 = ItemOptionFactory(price=100, item=self.item, name='Gold')
        self.bought_item1 = BoughtItem.objects.create(item_option=self.item_option1, order=self.order, price=Decimal(0), status=BoughtItem.BOUGHT)
        self.bought_item2 = BoughtItem.objects.create(item_option=self.item_option2, order=self.order, price=Decimal(0), status=BoughtItem.BOUGHT)
        self.txn = TransactionFactory(amount=Decimal("20"), order=self.order)
        self.txn.bought_items.add(self.bought_item1, self.bought_item2)

    def test_exclude_refunded_items(self):
        self.bought_item1.status = BoughtItem.REFUNDED
        self.bought_item1.save()

        data = {
            'items': [self.bought_item1.pk, self.bought_item2.pk],
        }

        form = TransactionRefundForm(self.txn, data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['items'], [self.bought_item2])

    def test_excessive_refund(self):
        data = {
            'amount': "25"
        }
        form = TransactionRefundForm(self.txn, data)
        self.assertEqual(len(form.errors.get('amount', [])), 1)

    def test_allow_no_values(self):
        "Form submits even is amount and items are unset"
        data = {}
        form = TransactionRefundForm(self.txn, data)
        self.assertTrue(form.is_valid())

    def test_disallow_zero_values(self):
        "Form fails is both items and amount are zero"
        data = {
            'items': [],
            'amount': Decimal("0")
        }
        form = TransactionRefundForm(self.txn, data)
        self.assertEqual(len(form.non_field_errors()), 1)

    def test_form_items_are_txn_items(self):
        form = TransactionRefundForm(self.txn)
        self.assertQuerysetEqual(form.fields['items'].queryset, [repr(r) for r in self.txn.bought_items.all()])  # WHY

    def test_alien_item_refund(self):
        alien_order = OrderFactory(event=self.event, person=self.person)
        alien_item = BoughtItem.objects.create(item_option=self.item_option1, price=Decimal(0), status=BoughtItem.BOUGHT, order=alien_order)
        data = {
            'items': [alien_item.pk]
        }
        form = TransactionRefundForm(self.txn, data)
        self.assertEqual(len(form.errors.get('items', [])), 1)
