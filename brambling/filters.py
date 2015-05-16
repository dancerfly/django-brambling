import copy

from django.db import models
from django.utils.datastructures import SortedDict
from django.utils.text import capfirst
from django.utils.translation import ugettext as _
import django_filters
import floppyforms.__future__ as forms
from floppyforms.__future__.models import FORMFIELD_OVERRIDES
import six

from brambling.forms.organizer import AttendeeFilterSetForm
from brambling.models import Attendee, Order, BoughtItem


FILTER_FIELD_OVERRIDES = copy.deepcopy(FORMFIELD_OVERRIDES)
FILTER_FIELD_OVERRIDES[models.BooleanField] = {'form_class': forms.NullBooleanField}


class BoughtItemStatusFilter(django_filters.BooleanFilter):
    field_class = forms.NullBooleanField

    def __init__(self, status, prefix='', *args, **kwargs):
        self.status = status
        self.prefix = prefix
        self.suffix = '__exact' if isinstance(status, basestring) else '__in'
        super(BoughtItemStatusFilter, self).__init__(status)

    def filter(self, qs, value):
        if value is None:
            return qs
        kwargs = {
            '{}bought_items__status{}'.format(self.prefix, self.suffix): self.status,
        }
        if value:
            return qs.filter(**kwargs)
        return qs.exclude(**kwargs)


class FloppyFilterSet(django_filters.FilterSet):
    class Meta:
        form = forms.Form

    @classmethod
    def filter_for_field(cls, f, name):
        filter_ = super(FloppyFilterSet, cls).filter_for_field(f, name)
        filter_.field_class = FILTER_FIELD_OVERRIDES[f.__class__]['form_class']
        return filter_

    def get_ordering_field(self):
        # Copied from django_filter. But in this context, uses floppyforms.
        if self._meta.order_by:
            if isinstance(self._meta.order_by, (list, tuple)):
                if isinstance(self._meta.order_by[0], (list, tuple)):
                    # e.g. (('field', 'Display name'), ...)
                    choices = [(f[0], f[1]) for f in self._meta.order_by]
                else:
                    choices = [(f, _('%s (descending)' % capfirst(f[1:])) if f[0] == '-' else capfirst(f))
                               for f in self._meta.order_by]
            else:
                # add asc and desc field names
                # use the filter's label if provided
                choices = []
                for f, fltr in self.filters.items():
                    choices.extend([
                        (fltr.name or f, fltr.label or capfirst(f)),
                        ("-%s" % (fltr.name or f), _('%s (descending)' % (fltr.label or capfirst(f))))
                    ])
            return forms.ChoiceField(label="Ordering", required=False,
                                     choices=choices)


class AttendeeFilterSet(django_filters.FilterSet):
    """
    FilterSet for attendees of an event. Requires the event as its first argument.

    """
    has_cart_items = BoughtItemStatusFilter(status=[BoughtItem.RESERVED, BoughtItem.UNPAID])
    has_purchased_items = BoughtItemStatusFilter(status=BoughtItem.BOUGHT)
    has_refunded_items = BoughtItemStatusFilter(status=BoughtItem.REFUNDED)

    def __init__(self, event, *args, **kwargs):
        "Limit the Item Option list to items belonging to this event."

        super(AttendeeFilterSet, self).__init__(*args, **kwargs)
        self.event = event
        if not event.collect_housing_data:
            del self.filters['housing_status']

    @property
    def form(self):
        # 1. Don't override custom filter fields :-p
        # 2. Don't override custom ordering field
        # 3. Pass in self.event
        if not hasattr(self, '_form'):
            fields = SortedDict([
                (name, filter_.field)
                for name, filter_ in six.iteritems(self.filters)
                if not name in self._meta.form.base_fields])
            Form = type(str('%sForm' % self.__class__.__name__),
                        (self._meta.form,), fields)
            if self.is_bound:
                self._form = Form(data=self.data, event=self.event, prefix=self.form_prefix)
            else:
                self._form = Form(event=self.event, prefix=self.form_prefix)
        return self._form

    class Meta:
        model = Attendee
        form = AttendeeFilterSetForm
        fields = ['bought_items__item_option', 'housing_status',
                  'bought_items__discounts__discount']
        order_by = ['surname', '-surname', 'given_name', '-given_name']


class OrderFilterSet(FloppyFilterSet):
    has_cart_items = BoughtItemStatusFilter(status=[BoughtItem.RESERVED, BoughtItem.UNPAID])
    has_purchased_items = BoughtItemStatusFilter(status=BoughtItem.BOUGHT)
    has_refunded_items = BoughtItemStatusFilter(status=BoughtItem.REFUNDED)

    class Meta:
        model = Order
        fields = ['providing_housing', 'send_flyers']
        form = forms.Form
        order_by = ['code', '-code']
# Workaround for https://github.com/gregmuellegger/django-floppyforms/issues/145
forms.MultipleChoiceField.hidden_widget = forms.MultipleHiddenInput
