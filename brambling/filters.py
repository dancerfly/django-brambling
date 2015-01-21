import copy

from django.db import models
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


class AttendeeFilterSet(django_filters.FilterSet):
    """
    FilterSet for attendees of an event. Requires the event as its first argument.

    """

    def __init__(self, event, *args, **kwargs):
        "Limit the Item Option list to items belonging to this event."

        super(AttendeeFilterSet, self).__init__(*args, **kwargs)
        self.event = event
        self.filters['bought_items__item_option'].extra.update({
            'queryset': ItemOption.objects.filter(item__event=self.event),
            'empty_label': 'Any Items',
        })
        self.filters['bought_items__discounts__discount'].extra.update({
            'queryset': Discount.objects.filter(event=self.event),
            'empty_label': 'Any Discounts',
        })
        if not event.collect_housing_data:
            del self.filters['housing_status']

    @property
    def form(self):
        if not hasattr(self, '_form'):
            if self.is_bound:
                self._form = AttendeeFilterSetForm(self.data, prefix=self.form_prefix)
            else:
                self._form = AttendeeFilterSetForm(prefix=self.form_prefix)
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
OrderFilterSet.base_filters['status'].field_class = forms.MultipleChoiceField
