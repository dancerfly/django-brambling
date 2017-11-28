import datetime

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.utils import timezone

from brambling.utils.model_tables import (
    AttendeeTable,
    TABLE_COLUMN_FIELD,
)
from brambling.models import CustomFormEntry
from brambling.tests.factories import (
    AttendeeFactory,
    CustomFormFactory,
    CustomFormFieldFactory,
    EnvironmentalFactorFactory,
    EventFactory,
    HousingCategoryFactory,
    HousingRequestNightFactory,
    ItemFactory,
    ItemOptionFactory,
    OrderFactory,
    TransactionFactory,
)
from brambling.utils.timezones import format_as_localtime


class AttendeeTableTestCase(TestCase):

    def setUp(self):
        self.event = EventFactory(collect_housing_data=True)
        self.item = ItemFactory(event=self.event)
        self.item_option = ItemOptionFactory(price=100, item=self.item)

        self.order = OrderFactory(event=self.event)
        self.transaction = TransactionFactory(
            event=self.event,
            order=self.order,
        )
        self.order.add_to_cart(self.item_option)
        self.order.mark_cart_paid(self.transaction)

        self.attendee = AttendeeFactory(
            order=self.order,
            bought_items=self.order.bought_items.all(),
            housing_status='have',
            email='something@example.com',
            other_needs='99 mattresses',
            person_avoid='Darth Vader',
            person_prefer='Lando Calrissian',
        )
        self.attendee.ef_cause = [
            EnvironmentalFactorFactory(name='Laughter'),
            EnvironmentalFactorFactory(name='Confusion'),
        ]
        self.attendee.housing_prefer = [
            HousingCategoryFactory(name='Yurt'),
        ]
        self.attendee.ef_avoid = [
            EnvironmentalFactorFactory(name='Ontology'),
            EnvironmentalFactorFactory(name='Gnosticism'),
        ]
        self.attendee.nights.add(HousingRequestNightFactory(date=self.event.start_date))

        attendee_form = CustomFormFactory(event=self.event, form_type='attendee')
        f1 = CustomFormFieldFactory(form=attendee_form, name='favorite color')
        self.custom_key1 = f1.key
        entry1 = CustomFormEntry.objects.create(
            related_ct=ContentType.objects.get(model='attendee'),
            related_id=self.attendee.id,
            form_field=f1)
        entry1.set_value('ochre')
        entry1.save()

        housing_form = CustomFormFactory(event=self.event, form_type='housing')
        f2 = CustomFormFieldFactory(form=housing_form, name='floor or bed')
        self.custom_key2 = f2.key
        entry2 = CustomFormEntry.objects.create(
            related_ct=ContentType.objects.get(model='attendee'),
            related_id=self.attendee.pk,
            form_field=f2)
        entry2.set_value('bed')
        entry2.save()

    def test_blank_housing_fields_if_attendee_does_not_need_housing(self):
        table = AttendeeTable(self.event)

        for row in table:
            self.assertEqual(row['other_needs_if_needed'].value, '')
            self.assertEqual(row['housing_nights'].value, '')
            self.assertEqual(row['housing_preferences'].value, '')
            self.assertEqual(row['environment_avoid'].value, '')
            self.assertEqual(row['environment_cause'].value, '')
            self.assertEqual(row['person_prefer_if_needed'].value, '')
            self.assertEqual(row['person_avoid_if_needed'].value, '')
            self.assertEqual(row[self.custom_key2].value, '')

    def test__show_non_housing_form_data_if_attendee_needs_housing(self):
        table = AttendeeTable(self.event)
        for row in table:
            self.assertEqual(row[self.custom_key1].value, 'ochre')

    def test_show_non_housing_form_data_if_attendee_does_not_need_housing(self):
        self.attendee.housing_status = 'need'
        self.attendee.save()
        table = AttendeeTable(self.event)
        for row in table:
            self.assertEqual(row[self.custom_key1].value, 'ochre')

    def test_filled_housing_fields_if_attendee_needs_housing(self):
        self.attendee.housing_status = 'need'
        self.attendee.save()
        table = AttendeeTable(self.event)

        for row in table:
            self.assertNotEqual(row['other_needs_if_needed'].value, '')
            self.assertNotEqual(row['housing_nights'].value, '')
            self.assertNotEqual(row['housing_preferences'].value, '')
            self.assertNotEqual(row['environment_avoid'].value, '')
            self.assertNotEqual(row['environment_cause'].value, '')
            self.assertNotEqual(row['person_prefer_if_needed'].value, '')
            self.assertNotEqual(row['person_avoid_if_needed'].value, '')
            self.assertNotEqual(row[self.custom_key2].value, '')

    def test_purchase_date_field(self):
        table = AttendeeTable(
            event=self.event,
            data={
                TABLE_COLUMN_FIELD: ['pk', 'purchase_date'],
            },
        )
        row = list(table)[0]
        self.assertEqual(
            row['purchase_date'].value,
            format_as_localtime(
                self.transaction.timestamp,
                '%Y-%m-%d %H:%M',
                self.event.timezone,
            ),
        )

    def test_order_by_purchase_date(self):
        """
        If ordering by purchase date is selected, we should get that
        ordering even if the field isn't selected.

        """
        order2 = OrderFactory(event=self.event)
        transaction = TransactionFactory(
            event=self.event,
            order=order2,
            timestamp=timezone.now() - datetime.timedelta(days=50)
        )
        order2.add_to_cart(self.item_option)
        order2.mark_cart_paid(transaction)
        attendee2 = AttendeeFactory(
            order=order2,
            bought_items=order2.bought_items.all(),
            housing_status='have',
            email='leia@example.com',
            other_needs='99 mattresses',
            person_avoid='Darth Vader',
            person_prefer='Han Solo',
        )

        table = AttendeeTable(
            event=self.event,
            data={
                'o': '-purchase_date',
                TABLE_COLUMN_FIELD: ['pk', 'get_full_name'],
            },
        )
        rows = list(table)
        self.assertEqual(rows[0]['pk'].value, self.attendee.pk)
        self.assertEqual(rows[1]['pk'].value, attendee2.pk)
