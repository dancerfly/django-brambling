from collections import OrderedDict
import csv
import datetime
import itertools

from django.contrib.admin.utils import lookup_field
from django.contrib.admin.views.main import EMPTY_CHANGELIST_VALUE
from django.db.models import Sum
from django.http import StreamingHttpResponse
from django.utils.encoding import force_text
import floppyforms as forms
from zenaida.templatetags.zenaida import format_money


__all__ = ('comma_separated_manager', 'ModelTable',
           'AttendeeTable')


TABLE_COLUMN_FIELD = 'columns'


class Echo(object):
    """
    An object that implements just the write method of the file-like
    interface.

    See https://docs.djangoproject.com/en/dev/howto/outputting-csv/#streaming-csv-files
    """
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


def comma_separated_manager(attr_name):
    """
    Returns a function which takes a M2M manager on an object and
    returns it as a comma separated string.

    """

    def inner(self, obj):
        manager = getattr(obj, attr_name)
        return ", ".join([unicode(x) for x in manager.all()])
    return inner


class Cell(object):
    def __init__(self, field, value):
        self.field = field
        self.value = value

    def __unicode__(self):
        return unicode(self.value)

    def __repr__(self):
        return u"{}: {}".format(self.field, self.value)

    def is_boolean(self):
        return isinstance(self.value, bool)


class Row(object):
    def __init__(self, data, obj=None):
        self.data = OrderedDict(data)
        self.obj = obj

    def __getitem__(self, key):
        if isinstance(key, int):
            return Cell(*self.data.items()[key])
        return Cell(key, self.data[key])

    def __iter__(self):
        for key, value in self.data.items():
            yield Cell(key, value)

    def __len__(self):
        return len(self.data)


class ModelTable(object):
    """
    A class that is responsible for taking a queryset and building a table
    out of it, useful for allowing the customization of which columns of data
    to display. This table can be used in a template context or rendered
    directly as a CSV document.

    It takes three arguments:

    1. The queryset to be displayed
    2. Data
    3. A form prefix

    """

    #: The fields as a list of 3-tuples of the format
    #: ("Field Verbose Name", "field_name", default), where default is True
    #: or False (indicating whether the field should be included by default).
    #: `field_name` can be the name of an attribute on the model
    #: or an attribute on the ModelTable subclass.
    fields = ()

    def __init__(self, queryset, data=None, form_prefix=None):
        # Simple assignment:
        self.data = data or {}
        self.queryset = queryset
        self.form_prefix = form_prefix

        # More complex properties:
        self.is_bound = data is not None

    def __iter__(self):
        object_list = self.get_queryset()
        for obj in object_list:
            yield Row(((field[1], self.get_field_val(obj, field[1]))
                       for field in self.get_included_fields()),
                      obj=obj)

    def header_row(self):
        return Row((field[1], field[0])
                   for field in self.get_included_fields())

    def get_fields(self):
        """
        Returns a full list of fields that users can select from.
        """
        return self.fields

    def get_included_fields(self):
        """
        Returns a tuple of 2-tuples in the form of
        ("Field Verbose Name", "field_name").

        """
        valid = self.is_bound and self.form.is_valid()
        if valid:
            cleaned_data = self.form.cleaned_data
            # Include fields which are marked True in the form:
            fields = [field
                      for field in self.get_fields()
                      if field[1] in cleaned_data.get(TABLE_COLUMN_FIELD, ())]
            # Only return a list of fields if it isn't empty:
            if not fields == []:
                return fields
        # Otherwise default to all fields:
        return self.get_fields()

    def get_queryset(self):
        return self.queryset

    def get_field_val(self, obj, key):
        """
        Follows the same rules as ModelAdmin dynamic lookups:

        1. Model field
        2. Callable
        3. Method on table
        4. Method on model
        5. Other attribute on model

        Returns a value which will be passed to the template.
        """
        # Compare:
        # * django.contrib.admin.utils:display_for_field
        # * django.contrib.admin.utils:display_for_value
        field, attr, value = lookup_field(key, obj, self)

        if field is not None:
            if field.flatchoices:
                # EMPTY_CHANGELIST_VALUE is "(None)"
                return dict(field.flatchoices).get(value, EMPTY_CHANGELIST_VALUE)

        return value

    def get_form_class(self):
        return forms.Form

    @property
    def form(self):
        """
        Returns a form of booleans for each field in fields,
        bound with self.data if is not None.

        """

        if not hasattr(self, '_form'):
            fields = self.get_fields()
            choices = [(field[1], field[0]) for field in fields]
            initial = [field[1] for field in fields if field[2]]
            field = forms.MultipleChoiceField(
                choices=choices,
                initial=initial,
                widget=forms.CheckboxSelectMultiple,
                required=False,
            )
            fields = {
                TABLE_COLUMN_FIELD: field,
            }

            Form = type(str('{}Form'.format(self.__class__.__name__)), (self.get_form_class(),), fields)

            if self.is_bound:
                self._form = Form(self.data, prefix=self.form_prefix)
            else:
                self._form = Form(prefix=self.form_prefix)

        return self._form

    def render_csv_response(self):
        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer)
        response = StreamingHttpResponse((writer.writerow([force_text(cell.value) for cell in row])
                                          for row in itertools.chain((self.header_row(),), self)),
                                         content_type="text/csv")
        response['Content-Disposition'] = 'attachment; filename="export.csv"'
        return response


class CustomDataTable(ModelTable):
    def get_custom_fields(self):
        if not hasattr(self, 'custom_fields'):
            self.custom_fields = self._get_custom_fields()
        return tuple(
            (field.name, field.key, True)
            for field in self.custom_fields
        )

    def _get_custom_fields(self):
        raise NotImplementedError

    def get_field_val(self, obj, key):
        if key[0:7] == 'custom_':
            if not hasattr(obj, '_custom_data'):
                raw_data = {
                    entry.form_field_id: entry.get_value()
                    for entry in obj.custom_data.all()
                }
                obj._custom_data = {
                    field.key: raw_data[field.pk]
                    for field in self.custom_fields
                    if field.pk in raw_data
                }
            return obj._custom_data.get(key, '')
        return super(CustomDataTable, self).get_field_val(obj, key)


class AttendeeTable(CustomDataTable):

    #: A list of ID related fields.
    IDENTIFICATION_FIELD_OPTIONS = (
        ("ID", "pk", True),
        ("Name", "get_full_name", True),
        ("Given Name", "given_name", True),
        ("Surname", "surname", True),
        ("Middle Name", "middle_name", True),
    )

    #: A list of contact related fields.
    CONTACT_FIELD_OPTIONS = (
        ("Email Address", "email", True),
        ("Phone Number", "phone", True),
    )

    #: A list of pass fields.
    PASS_FIELD_OPTIONS = (
        ("Pass Type", "pass_type", True),
        ("Pass Status", "pass_status", True),
    )

    #: A list of housing related fields.
    HOUSING_FIELD_OPTIONS = (
        ("Housing Status", "housing_status", True),
        ("Housing Nights", "housing_nights", True),
        ("Housing Environment Preference", "housing_preferences", True),
        ("Housing Environment Avoid", "environment_avoid", True),
        ("Attendee May Cause/Do", "environment_cause", True),
        ("Housing People Preference", "person_prefer", True),
        ("Housing People Avoid", "person_avoid", True),
        ("Other Housing Needs", "other_needs", True),
    )

    #: A list of order related fields.
    ORDER_FIELD_OPTIONS = (
        ("Order Code", "order_code", True),
        ("Order Placed By", "order_placed_by", True),
        ("Order Balance", "order_balance", True),
        ("Order Item Count", "order_item_count", True),
    )

    #: A list of miscellaneous fields.
    MISCELLANEOUS_FIELD_OPTIONS = (
        ("Liability Waiver Signed", "liability_waiver", True),
        ("Consent to be Photographed", "photo_consent", True),
    )

    def __init__(self, event, *args, **kwargs):
        self.event = event
        super(AttendeeTable, self).__init__(*args, **kwargs)

    def get_fields(self):
        fields = (
            self.IDENTIFICATION_FIELD_OPTIONS,
            self.CONTACT_FIELD_OPTIONS,
            self.PASS_FIELD_OPTIONS,
        )
        if self.event.collect_housing_data:
            fields += (
                self.HOUSING_FIELD_OPTIONS,
            )
        fields += (
            self.ORDER_FIELD_OPTIONS,
            self.MISCELLANEOUS_FIELD_OPTIONS,
        )

        fields += (self.get_custom_fields(),)

        return reduce(tuple.__add__, fields)

    def _get_custom_fields(self):
        from brambling.models import CustomForm, CustomFormField
        return CustomFormField.objects.filter(
            form__event=self.event,
            form__form_type=CustomForm.ATTENDEE
        ).order_by('index')

    def get_queryset(self):
        qs = super(AttendeeTable, self).get_queryset()
        return qs.prefetch_related(
            'custom_data', 'nights', 'housing_prefer', 'ef_avoid', 'ef_cause'
        ).select_related(
            'order', 'order__person', 'event_pass__item_option__item'
        ).annotate(
            order_balance=Sum('order__transactions__amount')
        ).extra(select={
            'order_item_count': """
SELECT COUNT(*) FROM brambling_boughtitem WHERE
brambling_boughtitem.order_id = brambling_order.id AND
brambling_boughtitem.status != 'refunded'
"""
        })

    # Methods to be used as fields
    def order_code(self, obj):
        return obj.order.code

    def order_status(self, obj):
        return obj.order.get_status_display()

    def order_placed_by(self, obj):
        person = obj.order.person
        if person:
            return "{} ({})".format(person.get_full_name(), person.email)
        return ""

    def pass_type(self, obj):
        return "{}: {}".format(
            obj.event_pass.item_option.item.name,
            obj.event_pass.item_option.name)

    def pass_status(self, obj):
        return obj.event_pass.get_status_display()

    def order_balance(self, obj):
        return format_money(obj.order_balance or 0, self.event.currency)

    housing_nights = comma_separated_manager("nights")
    housing_preferences = comma_separated_manager("housing_prefer")
    environment_avoid = comma_separated_manager("ef_avoid")
    environment_cause = comma_separated_manager("ef_cause")


class OrderTable(CustomDataTable):
    BASE_FIELDS = (
        ("Code", "code", True),
        ("Person", "person", True),
        ("Balance", "balance", True),
        ("Item Count", "item_count", True),
    )

    SURVEY_FIELDS = (
        ("Heard Through", "heard_through", True),
        ("Heard Through (Other)", "heard_through_other", True),
        ("Send Flyers", "send_flyers", True),
        ("Flyers Address", "send_flyers_full_address", True),
    )

    HOUSING_FIELDS = (
        ("Providing housing", "providing_housing", True),
        ("Hosting Contact name", "contact_name", True),
        ("Hosting Contact email", "contact_email", True),
        ("Hosting Contact phone", "contact_phone", True),
        ("Hosting Address", "hosting_full_address", True),
        ("Hosting Public transit access", "public_transit_access", True),
        ("Hosting Environmental Factors", "ef_present", True),
        ("Hosting Environmental Factors Avoided", "ef_avoid", True),
        ("Hosting People Preference", "person_prefer", True),
        ("Hosting People Avoid", "person_avoid", True),
        ("Hosting Home Categories", "housing_categories", True),
    )

    def __init__(self, event, *args, **kwargs):
        self.event = event
        super(OrderTable, self).__init__(*args, **kwargs)

    def get_fields(self):
        fields = self.BASE_FIELDS
        if self.event.collect_survey_data:
            fields += self.SURVEY_FIELDS
        if self.event.collect_housing_data:
            fields += self.HOUSING_FIELDS
            for date in self.event.housing_dates.all():
                fields += (
                    ("Hosting {} spaces".format(date.date.strftime("%m/%d/%Y")), "hosting_spaces_{}".format(date.date.strftime("%Y%m%d")), True),
                    ("Hosting {} max".format(date.date.strftime("%m/%d/%Y")), "hosting_max_{}".format(date.date.strftime("%Y%m%d")), True),
                )

        fields += self.get_custom_fields()
        return fields

    def get_queryset(self):
        qs = super(OrderTable, self).get_queryset()
        return qs.prefetch_related(
            'custom_data',
        ).annotate(
            balance=Sum('transactions__amount')
        ).extra(select={
            'item_count': """
SELECT COUNT(*) FROM brambling_boughtitem WHERE
brambling_boughtitem.order_id = brambling_order.id AND
brambling_boughtitem.status != 'refunded'
"""
        })

    def _get_custom_fields(self):
        from brambling.models import CustomForm, CustomFormField
        return CustomFormField.objects.filter(
            form__event=self.event,
            form__form_type=CustomForm.ORDER
        ).order_by('index')

    def get_field_val(self, obj, key):
        date_str = None
        from brambling.models import HousingSlot

        if key.startswith('hosting_max'):
            date_str = key[-8:]
            field = "spaces_max"
        elif key.startswith('hosting_spaces'):
            date_str = key[-8:]
            field = "spaces"

        if date_str:
            if obj.get_eventhousing():
                hosting_date = datetime.datetime.strptime(date_str, "%Y%m%d").date()
                try:
                    slot = HousingSlot.objects.get(eventhousing__order=obj, night__date=hosting_date)
                except HousingSlot.DoesNotExist:
                    pass
                else:
                    return getattr(slot, field, '')
            return ''
        return super(OrderTable, self).get_field_val(obj, key)

    def send_flyers_full_address(self, obj):
        if obj.send_flyers:
            return u", ".join((
                obj.send_flyers_address,
                obj.send_flyers_address_2,
                obj.send_flyers_city,
                obj.send_flyers_state_or_province,
                obj.send_flyers_zip,
                unicode(obj.send_flyers_country),
            ))
        return ''

    def hosting_full_address(self, obj):
        eventhousing = obj.get_eventhousing()
        if eventhousing:
            return u", ".join((
                eventhousing.address,
                eventhousing.address_2,
                eventhousing.city,
                eventhousing.state_or_province,
                eventhousing.zip_code,
                unicode(eventhousing.country),
            ))
        return ''

    def get_eventhousing_attr(self, obj, name):
        eventhousing = obj.get_eventhousing()
        if eventhousing:
            return getattr(eventhousing, name)
        return ''

    def contact_name(self, obj):
        return self.get_eventhousing_attr(obj, 'contact_name')

    def contact_email(self, obj):
        return self.get_eventhousing_attr(obj, 'contact_email')

    def contact_phone(self, obj):
        return self.get_eventhousing_attr(obj, 'contact_phone')

    def public_transit_access(self, obj):
        return self.get_eventhousing_attr(obj, 'public_transit_access')

    def person_prefer(self, obj):
        return self.get_eventhousing_attr(obj, 'person_prefer')

    def person_avoid(self, obj):
        return self.get_eventhousing_attr(obj, 'person_avoid')

    def get_eventhousing_csm(self, obj, name):
        eventhousing = obj.get_eventhousing()
        if eventhousing:
            return comma_separated_manager(name)(self, eventhousing)
        return ''

    def ef_present(self, obj):
        return self.get_eventhousing_csm(obj, 'ef_present')

    def ef_avoid(self, obj):
        return self.get_eventhousing_csm(obj, 'ef_avoid')

    def housing_categories(self, obj):
        return self.get_eventhousing_csm(obj, 'housing_categories')

    def balance(self, obj):
        return format_money(obj.balance or 0, self.event.currency)
