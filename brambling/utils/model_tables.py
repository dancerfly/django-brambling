from collections import OrderedDict
import datetime
import operator

from django.contrib.admin.utils import (lookup_field, lookup_needs_distinct,
                                        label_for_field)
from django.contrib.admin.views.main import EMPTY_CHANGELIST_VALUE
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q, Sum, Min, Prefetch
from django.forms.forms import pretty_name
from django.utils.datastructures import SortedDict
from django.utils.text import capfirst
import floppyforms as forms
from zenaida.templatetags.zenaida import format_money
import six

from brambling.filters import FloppyFilterSet, AttendeeFilterSet, OrderFilterSet
from brambling.models import Attendee, Order, BoughtItem, Transaction
from brambling.utils.timezones import format_as_localtime


__all__ = ('related_objects_list', 'ModelTable',
           'AttendeeTable')


TABLE_COLUMN_FIELD = 'columns'
SEARCH_FIELD = 'search'


class Echo(object):
    """
    An object that implements just the write method of the file-like
    interface.

    See https://docs.djangoproject.com/en/dev/howto/outputting-csv/#streaming-csv-files
    """
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


class Cell(object):
    def __init__(self, field, value):
        self.field = field
        self.value = value

    def __unicode__(self):
        """
        Return a comma-separated list if value is an iterable. Otherwise, return
        the value as a string.

        """

        if self.is_iterable():
            return u"\n".join([unicode(x) for x in self.value])
        return unicode(self.value)

    def __repr__(self):
        return u"{}: {}".format(self.field, self.value)

    def is_boolean(self):
        return isinstance(self.value, bool)

    def is_iterable(self):
        return hasattr(self.value, '__iter__')


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
    A class that builds a customizable table representation of a model
    queryset. This representation is searchable, filterable, and has a
    customizable selection of fields. If data is not required, it will
    not be queried.

    The class takes three optional arguments on instantiation:

    1. Queryset
    2. Data
    3. A form prefix

    """

    list_display = ()
    default_fields = None
    search_fields = ()

    fieldsets = None

    #: A dictionary mapping field names to the overriding labels
    #: to be used for rendering this table.
    label_overrides = {}

    filterset_class = FloppyFilterSet
    model = None

    def __init__(self, queryset=None, data=None, form_prefix=None):
        # Simple assignment:
        self.queryset = queryset
        self.data = data
        self.form_prefix = form_prefix
        self.filterset = self.get_filterset()

        # More complex properties:
        self.is_bound = data is not None

    def __iter__(self):
        fields = self.get_fields()
        object_list = self.get_queryset(fields)
        for obj in object_list:
            yield Row(((field, self.get_field_val(obj, field))
                       for field in fields),
                      obj=obj)

    def __len__(self):
        fields = self.get_fields()
        object_list = self.get_queryset(fields)
        return object_list.count()

    def __nonzero__(self):
        # Prevents infinite recursion from calling __len__ - label_for_field
        # gets called during __len__, and checks the boolean value of the
        # table.
        return True

    def _label(self, field):
        """
        Returns a pretty name for the given field. First check is the
        label_overrides dict. Remaining checks follow the django admin's
        pattern (including, for example, short_description support.)

        """
        if field in self.label_overrides:
            return self.label_overrides[field]

        try:
            return label_for_field(field, self.model, self)
        except AttributeError:
            # Trust that it exists, for now.
            return pretty_name(field)

    def header_row(self):
        return Row((field, self._label(field))
                   for field in self.get_fields())

    def get_filterset_kwargs(self):
        return {
            'data': self.data,
            'prefix': self.form_prefix,
        }

    def get_filterset(self):
        return self.filterset_class(**self.get_filterset_kwargs())

    def get_list_display(self):
        if self.fieldsets is not None:
            list_display = ()
            for name, fields in self.fieldsets:
                list_display += fields
            return list_display
        return self.list_display

    def get_default_fields(self):
        return self.default_fields

    def get_fields(self):
        """
        Returns a tuple of fields that are included in the table.

        """
        valid = self.is_bound and self.column_form.is_valid()
        if valid:
            cleaned_data = self.column_form.cleaned_data
            # Include fields which are marked True in the form:
            fields = list(cleaned_data.get(TABLE_COLUMN_FIELD, ()))
            # Only return a list of fields if it isn't empty:
            if fields:
                return fields

        return self.column_form.fields[TABLE_COLUMN_FIELD].initial

    def get_base_queryset(self):
        if self.queryset is None:
            return self.model._default_manager.all()
        if self.queryset.model is not self.model:
            raise ImproperlyConfigured("QuerySet model must be the same as ModelTable model.")
        return self.queryset.all()

    def _add_data(self, queryset, fields):
        """
        Add data to the queryset based on the selected fields.

        For now, data required by filters should always be added.

        """
        use_distinct = False
        return queryset, use_distinct

    def _search(self, queryset):
        # Originally from django.contrib.admin.options
        def construct_search(field_name):
            if field_name.startswith('^'):
                return "%s__istartswith" % field_name[1:]
            elif field_name.startswith('='):
                return "%s__iexact" % field_name[1:]
            elif field_name.startswith('@'):
                return "%s__search" % field_name[1:]
            else:
                return "%s__icontains" % field_name

        use_distinct = False
        search_fields = self.search_fields
        search_term = self.data.get(SEARCH_FIELD, '') if self.data else ''
        opts = self.model._meta
        if search_fields and search_term:
            orm_lookups = [construct_search(str(search_field))
                           for search_field in search_fields]
            for bit in search_term.split():
                or_queries = [Q(**{orm_lookup: bit})
                              for orm_lookup in orm_lookups]
                queryset = queryset.filter(reduce(operator.or_, or_queries))
            if not use_distinct:
                for search_spec in orm_lookups:
                    if lookup_needs_distinct(opts, search_spec):
                        use_distinct = True
                        break
        return queryset, use_distinct

    def get_queryset(self, fields):
        queryset = self.get_base_queryset()

        queryset, use_distinct = self._add_data(queryset, fields)

        queryset, ud = self._search(queryset)

        if use_distinct or ud:
            queryset = queryset.distinct()

        # HACK to work around filterset qs caching
        if hasattr(self.filterset, '_qs'):
            del self.filterset._qs
        self.filterset.queryset = queryset
        return self.filterset.qs

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

    @property
    def empty_filter_form(self):
        if not hasattr(self, '_empty_filter_form'):
            filterset = self.filterset
            fields = SortedDict([
                (name, filter_.field)
                for name, filter_ in six.iteritems(filterset.filters)])
            fields[filterset.order_by_field] = filterset.ordering_field
            Form = type(str('%sForm' % filterset.__class__.__name__),
                        (filterset._meta.form,), fields)
            initial = dict(((name, None) for name in Form.base_fields))
            self._empty_filter_form = Form(prefix=filterset.form_prefix, initial=initial)
        return self._empty_filter_form

    @property
    def filter_form(self):
        return self.filterset.form

    def get_column_form_class(self):
        return forms.Form

    @property
    def column_form(self):
        """
        Returns a form of booleans for each field in fields,
        bound with self.data if is not None.

        """
        if not hasattr(self, '_column_form'):
            list_display = self.get_list_display()
            default_fields = self.get_default_fields()

            choices = [(field, capfirst(self._label(field))) for field in list_display]
            if default_fields is None:
                initial = list_display
            else:
                initial = default_fields
            field = forms.MultipleChoiceField(
                choices=choices,
                initial=initial,
                widget=forms.CheckboxSelectMultiple,
                required=False,
            )
            # Workaround for https://github.com/gregmuellegger/django-floppyforms/issues/145
            field.hidden_widget = forms.MultipleHiddenInput
            fields = {
                TABLE_COLUMN_FIELD: field,
            }

            Form = type(str('{}Form'.format(self.__class__.__name__)), (self.get_column_form_class(),), fields)

            self._column_form = Form(self.data, prefix=self.form_prefix)

        return self._column_form


class CustomDataTable(ModelTable):
    def get_list_display(self):
        list_display = super(CustomDataTable, self).get_list_display()
        return list_display + self.get_custom_fields()

    def get_default_fields(self):
        if self.default_fields is None:
            return None
        return self.default_fields + self.get_custom_fields()

    def get_custom_fields(self):
        if not hasattr(self, 'custom_fields'):
            self.custom_fields = self._get_custom_fields()
            for field in self.custom_fields:
                if field.key not in self.label_overrides:
                    self.label_overrides[field.key] = field.name
        return tuple(field.key for field in self.custom_fields)

    def _get_custom_data(self, obj):
        return {
            entry.form_field_id: entry.get_value()
            for entry in obj.custom_data.all()
        }

    def _get_custom_fields(self):
        raise NotImplementedError

    def get_field_val(self, obj, key):
        if key.startswith('custom_'):
            if not hasattr(obj, '_custom_data'):
                raw_data = self._get_custom_data(obj)
                obj._custom_data = {
                    field.key: raw_data[field.pk]
                    for field in self.custom_fields
                    if field.pk in raw_data
                }
            return obj._custom_data.get(key, '')
        return super(CustomDataTable, self).get_field_val(obj, key)


class AttendeeTable(CustomDataTable):
    fieldsets = (
        ('Identification',
         ('pk', 'get_full_name', 'given_name', 'surname', 'middle_name')),
        ('Status',
         ('items', 'purchase_date', 'pending', 'confirmed', 'order_code')),
        ('Contact',
         ('email', 'phone')),
        ('Housing',
         ('housing_status', 'housing_nights',
          'housing_preferences', 'environment_avoid',
          'environment_cause', 'person_prefer_if_needed',
          'person_avoid_if_needed', 'other_needs_if_needed')),
        ('Miscellaneous',
         ('liability_waiver', 'photo_consent', 'notes')),
    )

    label_overrides = {
        'pk': 'Id',
        'get_full_name': 'Name',
        'housing_nights': 'Housing nights',
        'housing_preferences': 'Housing environment preference',
        'environment_avoid': 'Housing Environment Avoid',
        'environment_cause': 'Attendee May Cause/Do',
        'person_prefer_if_needed': 'Housing People Preference',
        'person_avoid_if_needed': 'Housing People Avoid',
        'other_needs_if_needed': 'Other Housing Needs',
        'order_code': 'Order Code',
        'liability_waiver': 'Liability Waiver Signed',
        'photo_consent': 'Consent to be Photographed',
    }
    search_fields = ('given_name', 'middle_name', 'surname', 'order__code',
                     'email', 'order__email', 'order__person__email')
    filterset_class = AttendeeFilterSet
    model = Attendee

    def __init__(self, event, *args, **kwargs):
        self.event = event
        super(AttendeeTable, self).__init__(*args, **kwargs)

    def get_filterset_kwargs(self):
        kwargs = super(AttendeeTable, self).get_filterset_kwargs()
        kwargs['event'] = self.event
        return kwargs

    def _get_custom_fields(self):
        from brambling.models import CustomForm, CustomFormField
        qs = CustomFormField.objects.filter(
            form__event=self.event,
        ).order_by('index')
        if self.event.collect_housing_data:
            return qs.filter(form__form_type__in=(CustomForm.ATTENDEE, CustomForm.HOUSING))
        else:
            return qs.filter(form__form_type=CustomForm.ATTENDEE)

    def _add_data(self, queryset, fields):
        use_distinct = False
        queryset = queryset.prefetch_related(
            Prefetch(
                'bought_items',
                queryset=BoughtItem.objects.filter(status=BoughtItem.BOUGHT).prefetch_related(
                    Prefetch(
                        'transactions',
                        queryset=Transaction.objects.filter(is_confirmed=True),
                        to_attr='confirmed_transactions',
                    ),
                ),
                to_attr='items'
            ),
            'items__discounts',
        )
        for field in fields:
            if field.startswith('custom_'):
                queryset = queryset.prefetch_related('custom_data')
            elif field == 'housing_nights':
                queryset = queryset.prefetch_related('nights')
            elif field == 'housing_preferences':
                queryset = queryset.prefetch_related('housing_prefer')
            elif field == 'environment_avoid':
                queryset = queryset.prefetch_related('ef_avoid')
            elif field == 'environment_cause':
                queryset = queryset.prefetch_related('ef_cause')
            elif field == 'order_code':
                queryset = queryset.select_related('order')
            elif field == 'purchase_date':
                queryset = queryset.annotate(
                    purchase_date=Min('order__transactions__timestamp')
                )
        return queryset, use_distinct

    def _show_housing_data(self, attendee, form_entry):
        if form_entry.form_field.form.form_type != 'housing':
            return True
        if attendee.needs_housing():
            return True
        else:
            return False

    def _get_custom_data(self, attendee):
        return {
            entry.form_field_id: (entry.get_value() if self._show_housing_data(attendee, entry) else '')
            for entry in attendee.custom_data.select_related('form_field__form').all()
        }

    # Methods to be used as fields
    def order_code(self, obj):
        return obj.order.code

    def pending(self, obj):
        pending = 0
        for item in obj.items:
            if not item.confirmed_transactions:
                pending += item.price
                for discount in item.discounts.all():
                    pending -= discount.savings()
        return format_money(pending, self.event.currency)

    def confirmed(self, obj):
        confirmed = 0
        for item in obj.items:
            if item.confirmed_transactions:
                confirmed += item.price
                for discount in item.discounts.all():
                    confirmed -= discount.savings()
        return format_money(confirmed, self.event.currency)

    def housing_nights(self, attendee):
        return attendee.nights.all() if attendee.needs_housing() else ''

    def housing_preferences(self, attendee):
        return (attendee.housing_prefer.all() if attendee.needs_housing()
                else '')

    def environment_avoid(self, attendee):
        return attendee.ef_avoid.all() if attendee.needs_housing() else ''

    def environment_cause(self, attendee):
        return attendee.ef_cause.all() if attendee.needs_housing() else ''

    def person_prefer_if_needed(self, attendee):
        return attendee.person_prefer if attendee.needs_housing() else ''

    def person_avoid_if_needed(self, attendee):
        return attendee.person_avoid if attendee.needs_housing() else ''

    def other_needs_if_needed(self, attendee):
        return attendee.other_needs if attendee.needs_housing() else ''

    def items(self, obj):
        return ["{} ({})".format(x.item_option_name, x.item_name)
                for x in obj.items]

    def purchase_date(self, obj):
        if obj.purchase_date:
            return format_as_localtime(obj.purchase_date, '%Y-%m-%d %H:%M',
                                       self.event.timezone)
        else:
            return 'N/A'


class OrderTable(CustomDataTable):
    fieldsets = (
        (None,
         ('code', 'person', 'pending', 'confirmed',
          'purchased_items', 'refunded_items', 'completed_date', 'notes')),
    )
    survey_fieldsets = (
        ('Survey',
         ('heard_through', 'heard_through_other',
          'send_flyers', 'send_flyers_full_address')),
    )
    housing_fieldsets = (
        ('Housing',
         ('providing_housing', 'contact_name', 'contact_email',
          'contact_phone', 'hosting_full_address', 'public_transit_access',
          'ef_present', 'ef_avoid', 'person_prefer', 'person_avoid',
          'housing_categories')),
    )
    label_overrides = {
        'heard_through_other': 'heard through (other)',
        'send_flyers_full_address': 'flyers address',
    }
    search_fields = (
        'code', 'email', 'person__given_name', 'person__middle_name',
        'person__surname', 'person__email', 'attendees__given_name',
        'attendees__middle_name', 'attendees__surname',
    )
    filterset_class = OrderFilterSet
    model = Order

    def __init__(self, event, *args, **kwargs):
        self.event = event
        super(OrderTable, self).__init__(*args, **kwargs)

    def get_list_display(self):
        fieldsets = self.fieldsets
        if self.event.collect_survey_data:
            fieldsets += self.survey_fieldsets
        if self.event.collect_housing_data:
            housing_fields = self.housing_fieldsets[0][1]
            for date in self.event.get_housing_dates():
                housing_fields += (
                    "hosting_spaces_{}".format(date.strftime("%Y%m%d")),
                    "hosting_max_{}".format(date.strftime("%Y%m%d")),
                )
            fieldsets += (
                ('Housing', housing_fields),
            )

        fieldsets += (
            ('Custom Fields',
             self.get_custom_fields()),
        )
        list_display = ()
        for name, fields in fieldsets:
            list_display += fields
        return list_display

    def _get_custom_fields(self):
        from brambling.models import CustomForm, CustomFormField
        qs = CustomFormField.objects.filter(
            form__event=self.event,
        ).order_by('index')
        if self.event.collect_housing_data:
            return qs.filter(form__form_type__in=(CustomForm.ORDER, CustomForm.HOSTING))
        else:
            return qs.filter(form__form_type=CustomForm.ORDER)

    def _label(self, field):
        date_str = None
        if field.startswith('hosting_max'):
            date_str = field[-8:]
            format_str = "hosting {month}/{day}/{year} max"
        elif field.startswith('hosting_spaces'):
            date_str = field[-8:]
            format_str = "hosting {month}/{day}/{year} spaces"

        if date_str:
            return format_str.format(
                year=date_str[0:4],
                month=date_str[4:6],
                day=date_str[6:8]
            )
        return super(OrderTable, self)._label(field)

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
            if obj.get_eventhousing() and obj.providing_housing:
                hosting_date = datetime.datetime.strptime(date_str, "%Y%m%d").date()
                try:
                    slot = HousingSlot.objects.get(eventhousing__order=obj, date=hosting_date)
                except HousingSlot.DoesNotExist:
                    pass
                else:
                    return getattr(slot, field, '')
            return ''

        if key.startswith('custom_') and self.event.collect_housing_data and obj.providing_housing:
            if not hasattr(obj, '_custom_data'):
                super(OrderTable, self).get_field_val(obj, key)
                # Also include event_housing data.
                eventhousing = obj.get_eventhousing()
                if eventhousing:
                    raw_data = {
                        entry.form_field_id: entry.get_value()
                        for entry in eventhousing.custom_data.all()
                    }
                    obj._custom_data.update({
                        field.key: raw_data[field.pk]
                        for field in self.custom_fields
                        if field.pk in raw_data
                    })
            return obj._custom_data.get(key, '')
        return super(OrderTable, self).get_field_val(obj, key)

    def _add_data(self, queryset, fields):
        use_distinct = False
        queryset = queryset.annotate(
            completed_date=Min('transactions__timestamp'),
        ).prefetch_related('transactions')
        for field in fields:
            if field.startswith('custom_'):
                queryset = queryset.prefetch_related('custom_data')
            elif field == 'ef_present':
                queryset = queryset.prefetch_related('eventhousing__ef_present')
            elif field == 'ef_avoid':
                queryset = queryset.prefetch_related('eventhousing__ef_avoid')
            elif field == 'housing_categories':
                queryset = queryset.prefetch_related('eventhousing__housing_categories')
            elif field == 'person':
                queryset = queryset.select_related('person')
            elif field == 'purchased_items':
                queryset = queryset.extra(select={
                    'purchased_items': """
                        SELECT COUNT(*) FROM brambling_boughtitem WHERE
                        brambling_boughtitem.order_id = brambling_order.id AND
                        brambling_boughtitem.status = 'bought'
                    """,
                })
            elif field == 'refunded_items':
                queryset = queryset.extra(select={
                    'refunded_items': """
                        SELECT COUNT(*) FROM brambling_boughtitem WHERE
                        brambling_boughtitem.order_id = brambling_order.id AND
                        brambling_boughtitem.status = 'refunded'
                    """,
                })
        return queryset, use_distinct

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
        if eventhousing and obj.providing_housing:
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
        if eventhousing and obj.providing_housing:
            return getattr(eventhousing, name)
        return ''

    def contact_name(self, obj):
        return self.get_eventhousing_attr(obj, 'contact_name')
    contact_name.short_description = 'hosting contact name'

    def contact_email(self, obj):
        return self.get_eventhousing_attr(obj, 'contact_email')
    contact_email.short_description = 'hosting contact email'

    def contact_phone(self, obj):
        return self.get_eventhousing_attr(obj, 'contact_phone')
    contact_phone.short_description = 'hosting contact phone'

    def public_transit_access(self, obj):
        return self.get_eventhousing_attr(obj, 'public_transit_access')
    public_transit_access.short_description = 'hosting public transit access'

    def person_prefer(self, obj):
        return self.get_eventhousing_attr(obj, 'person_prefer')
    person_prefer.short_description = 'hosting people preference'

    def person_avoid(self, obj):
        return self.get_eventhousing_attr(obj, 'person_avoid')
    person_avoid.short_description = 'hosting people avoid'

    def ef_present(self, obj):
        return (obj.providing_housing and obj.get_eventhousing()) and obj.get_eventhousing().ef_present.all() or ''
    ef_present.short_description = 'hosting environmental factors'

    def ef_avoid(self, obj):
        return (obj.providing_housing and obj.get_eventhousing()) and obj.get_eventhousing().ef_avoid.all() or ''
    ef_avoid.short_description = 'hosting environmental avoided'

    def housing_categories(self, obj):
        return (obj.providing_housing and obj.get_eventhousing()) and obj.get_eventhousing().housing_categories.all() or ''
    housing_categories.short_description = 'hosting home categories'

    def pending(self, obj):
        pending = sum([txn.amount for txn in obj.transactions.all()
                       if not txn.is_confirmed])
        return format_money(pending, self.event.currency)

    def confirmed(self, obj):
        confirmed = sum([txn.amount for txn in obj.transactions.all()
                         if txn.is_confirmed])
        return format_money(confirmed, self.event.currency)

    def completed_date(self, obj):
        if obj.completed_date:
            return format_as_localtime(obj.completed_date, '%Y-%m-%d %H:%M',
                                       self.event.timezone)
        else:
            return 'N/A'
