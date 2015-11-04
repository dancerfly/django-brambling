from django.test import TestCase, RequestFactory
from django.utils import timezone

from brambling.forms.organizer import ManualPaymentForm, EventCreateForm
from brambling.models import Transaction
from brambling.tests.factories import (
    OrderFactory,
    PersonFactory,
    EventFactory,
    ItemFactory,
    ItemImageFactory,
    ItemOptionFactory,
    DiscountFactory,
    SavedReportFactory,
    CustomFormFactory,
    CustomFormFieldFactory,
    OrganizationFactory,
)


class ManualPaymentFormTestCase(TestCase):
    def test_creation(self):
        order = OrderFactory()
        user = PersonFactory()
        form = ManualPaymentForm(order=order, user=user, data={'amount': 10, 'method': Transaction.FAKE})
        self.assertFalse(form.errors)
        self.assertTrue(form.is_bound)
        txn = form.save()
        self.assertEqual(txn.amount, 10)
        self.assertEqual(txn.order, order)
        self.assertEqual(txn.event, order.event)
        self.assertEqual(txn.transaction_type, Transaction.PURCHASE)
        self.assertEqual(txn.method, Transaction.FAKE)
        self.assertEqual(txn.created_by, user)
        self.assertEqual(txn.is_confirmed, True)
        self.assertEqual(txn.api_type, order.event.api_type)


class EventCreateFormTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_duplication(self):
        """Passing in a template_event should result in settings and relevant related objects being copied"""
        template = EventFactory()
        item = ItemFactory(event=template)
        ItemOptionFactory(item=item)
        ItemImageFactory(item=item)
        DiscountFactory(event=template)
        SavedReportFactory(event=template)
        custom_form = CustomFormFactory(event=template)
        CustomFormFieldFactory(form=custom_form)

        request = self.factory.post('/', {
            'name': 'New event',
            'slug': 'new-event',
            'start_date': timezone.now().strftime("%Y-%m-%d"),
            'end_date': timezone.now().strftime("%Y-%m-%d"),
            'organization': str(template.organization.pk),
            'template_event': str(template.pk),
        })
        request.user = template.organization.owner
        form = EventCreateForm(request, data=request.POST)
        self.assertFalse(form.errors)
        event = form.save()

        fields = (
            'description', 'website_url', 'banner_image', 'city',
            'state_or_province', 'country', 'timezone', 'currency',
            'has_dances', 'has_classes', 'liability_waiver', 'privacy',
            'collect_housing_data', 'collect_survey_data', 'cart_timeout',
            'check_postmark_cutoff', 'transfers_allowed', 'facebook_url',
        )
        self.assertEqual(
            dict((f, getattr(event, f)) for f in fields),
            dict((f, getattr(template, f)) for f in fields)
        )
        # Make sure things haven't been moved off old events.
        self.assertEqual(template.items.count(), 1)
        item = template.items.all()[0]
        self.assertEqual(item.options.count(), 1)
        self.assertEqual(template.discount_set.count(), 1)
        self.assertEqual(template.savedreport_set.count(), 1)
        self.assertEqual(template.forms.count(), 1)
        custom_form = template.forms.all()[0]
        self.assertEqual(custom_form.fields.count(), 1)

        # Make sure things have been copied to new event.
        self.assertEqual(event.items.count(), 1)
        item = event.items.all()[0]
        self.assertEqual(item.options.count(), 1)
        self.assertEqual(event.discount_set.count(), 1)
        self.assertEqual(event.savedreport_set.count(), 1)
        self.assertEqual(event.forms.count(), 1)
        custom_form = event.forms.all()[0]
        self.assertEqual(custom_form.fields.count(), 1)
