from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.utils.timezone import now

from brambling.models import CustomFormEntry
from brambling.utils.model_tables import OrderTable
from brambling.tests.factories import (
    TransactionFactory, EventFactory, OrderFactory, ItemFactory,
    ItemOptionFactory, AttendeeFactory, EnvironmentalFactorFactory,
    HousingRequestNightFactory, HousingCategoryFactory, EventHousingFactory,
    HousingSlotFactory, CustomFormFactory, CustomFormFieldFactory)


class OrderTableTestCase(TestCase):

    def setUp(self):
        event = EventFactory(
            collect_housing_data=True,
            start_date=now().date() + timedelta(days=2),
            end_date=now().date() + timedelta(days=2)
        )
        order = OrderFactory(event=event, providing_housing=False)
        housing = EventHousingFactory(
            event=event, order=order, contact_name='Zardoz',
            contact_email='foobar@example.com', contact_phone='111-111-1111',
            public_transit_access=True, person_prefer='Han Solo',
            person_avoid='Greedo')
        HousingSlotFactory(eventhousing=housing, date=event.start_date,
                           spaces=1, spaces_max=1)
        HousingSlotFactory(eventhousing=housing,
                           date=event.start_date - timedelta(days=1),
                           spaces=1, spaces_max=1)
        housing.ef_present.add(EnvironmentalFactorFactory(name='Carbonite'))
        housing.ef_present.add(EnvironmentalFactorFactory(name='Sandbarges'))
        housing.ef_avoid.add(EnvironmentalFactorFactory(name='Jedi'))
        housing.ef_avoid.add(EnvironmentalFactorFactory(name='Droids'))
        housing.housing_categories.add(HousingCategoryFactory(name='Palace'))
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

        housing_form = CustomFormFactory(event=event, form_type='hosting')
        field = CustomFormFieldFactory(form=housing_form, name='bed condition')
        self.custom_key = field.key
        entry2 = CustomFormEntry.objects.create(
            related_ct=ContentType.objects.get(model='eventhousing'),
            related_id=housing.pk,
            form_field=field)
        entry2.set_value('unmade')
        entry2.save()

        self.event = event
        self.order = order

    def test_blank_housing_fields_if_attendee_does_not_provide_housing(self):
        table = OrderTable(self.event)
        for row in table:
            self.assertEqual(row['contact_name'].value, '')
            self.assertEqual(row['contact_email'].value, '')
            self.assertEqual(row['contact_phone'].value, '')
            self.assertEqual(row['public_transit_access'].value, '')
            self.assertEqual(row['person_prefer'].value, '')
            self.assertEqual(row['person_avoid'].value, '')
            self.assertEqual(row['ef_present'].value, '')
            self.assertEqual(row['ef_avoid'].value, '')
            self.assertEqual(row['housing_categories'].value, '')
            self.assertEqual(row[self.custom_key].value, '')
            for field in table.get_list_display():
                if field.startswith('hosting_'):
                    self.assertEqual(row[field].value, '')

    def test_filled_housing_fields_if_attendee_provides_housing(self):
        self.order.providing_housing = True
        self.order.save()
        table = OrderTable(self.event)
        for row in table:
            self.assertNotEqual(row['contact_name'].value, '')
            self.assertNotEqual(row['contact_email'].value, '')
            self.assertNotEqual(row['contact_phone'].value, '')
            self.assertNotEqual(row['public_transit_access'].value, '')
            self.assertNotEqual(row['person_prefer'].value, '')
            self.assertNotEqual(row['person_avoid'].value, '')
            self.assertNotEqual(row['ef_present'].value, '')
            self.assertNotEqual(row['ef_avoid'].value, '')
            self.assertNotEqual(row[self.custom_key].value, '')
            self.assertNotEqual(row['housing_categories'].value, '')
            for field in table.get_list_display():
                if field.startswith('hosting_spaces'):
                    self.assertNotEqual(row[field].value, '')
                if field.startswith('hosting_max'):
                    self.assertNotEqual(row[field].value, '')
