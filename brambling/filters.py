import copy

from django.db import models
from django.utils.text import capfirst
from django.utils.translation import ugettext as _
import django_filters
import floppyforms.__future__ as forms
from floppyforms.__future__.models import FORMFIELD_OVERRIDES

from brambling.forms.organizer import AttendeeFilterSetForm
from brambling.models import Attendee, ItemOption, Discount, Order


FILTER_FIELD_OVERRIDES = copy.deepcopy(FORMFIELD_OVERRIDES)
FILTER_FIELD_OVERRIDES[models.BooleanField] = {'form_class': forms.NullBooleanField}


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

    def __init__(self, event, *args, **kwargs):
        "Limit the Item Option list to items belonging to this event."

        super(AttendeeFilterSet, self).__init__(*args, **kwargs)
        self.event = event
        if not event.collect_housing_data:
            del self.filters['housing_status']

    @property
    def form(self):
        if not hasattr(self, '_form'):
            if self.is_bound:
                self._form = AttendeeFilterSetForm(data=self.data, event=self.event, prefix=self.form_prefix)
            else:
                self._form = AttendeeFilterSetForm(event=self.event, prefix=self.form_prefix)
        return self._form

    class Meta:
        model = Attendee
        fields = ['bought_items__item_option', 'housing_status',
                  'bought_items__discounts__discount']
        order_by = ['surname', '-surname', 'given_name', '-given_name']


class OrderFilterSet(FloppyFilterSet):
    status = django_filters.MultipleChoiceFilter(choices=Order.STATUS_CHOICES,
                                                 initial=[Order.COMPLETED, Order.PENDING])

    class Meta:
        model = Order
        fields = ['providing_housing', 'send_flyers', 'status']
        form = forms.Form
        order_by = ['code', '-code']
OrderFilterSet.base_filters['status'].field_class = forms.MultipleChoiceField
