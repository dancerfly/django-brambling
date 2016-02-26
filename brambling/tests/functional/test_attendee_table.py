from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from brambling.utils.model_tables import AttendeeTable
from brambling.models import CustomFormEntry
from brambling.tests.factories import (
    TransactionFactory, EventFactory, OrderFactory, ItemFactory,
    ItemOptionFactory, AttendeeFactory, EnvironmentalFactorFactory,
    HousingRequestNightFactory, HousingCategoryFactory, CustomFormFactory,
    CustomFormFieldFactory)


class AttendeeTableTestCase(TestCase):

    def setUp(self):
        event = EventFactory(collect_housing_data=True)
        order = OrderFactory(event=event)
        transaction = TransactionFactory(event=event, order=order)
        item = ItemFactory(event=event)
        item_option = ItemOptionFactory(price=100, item=item)

        order.add_to_cart(item_option)
        order.mark_cart_paid(transaction)

        self.attendee = AttendeeFactory(
            order=order,
            bought_items=order.bought_items.all(),
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
        self.attendee.nights.add(HousingRequestNightFactory(date=event.start_date))

        attendee_form = CustomFormFactory(event=event, form_type='attendee')
        f1 = CustomFormFieldFactory(form=attendee_form, name='favorite color')
        self.custom_key1 = f1.key
        entry1 = CustomFormEntry.objects.create(
            related_ct=ContentType.objects.get(model='attendee'),
            related_id=self.attendee.id,
            form_field=f1)
        entry1.set_value('ochre')
        entry1.save()

        housing_form = CustomFormFactory(event=event, form_type='housing')
        f2 = CustomFormFieldFactory(form=housing_form, name='floor or bed')
        self.custom_key2 = f2.key
        entry2 = CustomFormEntry.objects.create(
            related_ct=ContentType.objects.get(model='attendee'),
            related_id=self.attendee.pk,
            form_field=f2)
        entry2.set_value('bed')
        entry2.save()

        self.event = event

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
