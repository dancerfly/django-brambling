from collections import OrderedDict
from datetime import timedelta
from functools import wraps
from itertools import ifilter

import pytz
from django.core.urlresolvers import reverse
from django.db.models import Max, Min
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from zenaida.templatetags.zenaida import format_money

from brambling.models import Event, BoughtItem
from brambling.utils.model_tables import Cell, Row


def get_event_or_404(slug):
    qs = Event.objects.annotate(start_date=Min('dates__date'),
                                end_date=Max('dates__date'))
    return get_object_or_404(qs, slug=slug)


def route_view(test, if_true, if_false):
    # Redirects to if_true lazy reversal if condition is true and if_false
    # otherwise.
    def wrapped(request, *args, **kwargs):
        reversal = if_true if test(request, *args, **kwargs) else if_false
        return HttpResponseRedirect(reversal)
    return wrapped


class NavItem(object):
    def __init__(self, request, url, label, icon, disabled=False):
        self.request = request
        self.url = url
        self.label = label
        self.disabled = disabled
        self.icon = icon

    def is_active(self):
        return self.request.path.startswith(self.url)


def get_event_admin_nav(event, request):
    if not event.editable_by(request.user):
        return []
    return (
        {
            'name': 'General',
            'items': (
                ('brambling_event_basic', 'Basic Information'),
                ('brambling_event_permissions', 'Team & Permissions'),
                ('brambling_event_design', 'Design'),
                ('brambling_event_danger_zone', 'Copy Event'),
            ),
        },
        {
            'name': 'Registration',
            'items': (
                ('brambling_event_registration', 'Settings & Payment'),
                ('brambling_item_list', 'Items'),
                ('brambling_form_list', 'Forms'),
                ('brambling_discount_list', 'Discounts'),
            ),
        },
        {
            'name': 'Data',
            'items': (
                ('brambling_event_attendees', 'Attendees'),
                ('brambling_event_orders', 'Orders'),
                ('brambling_event_finances', 'Finances'),
            )
        },
    )


def get_organization_admin_nav(organization, request):
    if not organization.editable_by(request.user):
        return []
    kwargs = {
        'organization_slug': organization.slug,
    }
    items = (
        ('brambling_organization_update', 'Organization Profile', 'fa-institution'),
        ('brambling_organization_update_payment', 'Payment', 'fa-money'),
        ('brambling_organization_update_permissions', 'Permissions', 'fa-group'),
    )
    return [NavItem(request, reverse(view_name, kwargs=kwargs), label, icon)
            for view_name, label, icon in items]


def ajax_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.is_ajax():
            raise Http404
        return view(request, *args, **kwargs)
    return wrapped


def clear_expired_carts(event):
    expired_before = timezone.now() - timedelta(minutes=event.cart_timeout)
    BoughtItem.objects.filter(
        status=BoughtItem.RESERVED,
        order__event=event,
        order__cart_start_time__isnull=False,
        order__cart_start_time__lte=expired_before
    ).delete()


class Workflow(object):
    step_classes = []

    def __init__(self, **kwargs):
        if 'steps' in kwargs:
            raise ValueError("`steps` can't be passed as a kwarg value.")
        for k, v in kwargs.items():
            setattr(self, k, v)
        cls_iter = ifilter(lambda cls: cls.include_in(self), self.step_classes)
        self.steps = OrderedDict(((cls.slug, cls(self, index))
                                  for index, cls in enumerate(cls_iter)))

    @property
    def active_steps(self):
        return [step for step in self.steps.values()
                if step.is_active()]


class Step(object):
    name = None
    url = None
    slug = None

    @classmethod
    def include_in(cls, workflow):
        return True

    def __init__(self, workflow, index):
        self.workflow = workflow
        self.index = index

    @property
    def previous_step(self):
        for step in reversed(self.workflow.steps.values()[:self.index]):
            if step.is_active():
                return step
        return None

    @property
    def next_step(self):
        for step in self.workflow.steps.values()[self.index + 1:]:
            if step.is_active():
                return step
        return None

    def is_active(self):
        """Return False to indicate that the step should be ignored."""
        return True

    def is_accessible(self):
        if self.previous_step is None:
            return True
        return self.previous_step.is_completed()

    def is_completed(self):
        if not hasattr(self, '_completed'):
            self._completed = self._is_completed()
        return (self._completed and self.is_valid() and
                (self.previous_step is None or
                 self.previous_step.is_completed()))

    def _is_completed(self):
        raise NotImplementedError("_is_completed must be implemented by subclasses.")

    def is_valid(self):
        return not bool(self.errors)

    @property
    def errors(self):
        if not hasattr(self, '_errors'):
            self._errors = self.get_errors()
        return self._errors

    def get_errors(self):
        return []


class WorkflowMixin(object):
    current_step_slug = None
    workflow_class = None

    def get_reverse_kwargs(self):
        return self.kwargs

    def _reverse(self, view_name):
        return reverse(view_name, kwargs={
            key: value
            for key, value in self.get_reverse_kwargs().items()
            if value is not None
        })

    def dispatch(self, request, *args, **kwargs):
        self.workflow = self.get_workflow()
        if self.workflow is None or self.current_step_slug is None:
            self.current_step = None
        else:
            self.current_step = self.workflow.steps.get(self.current_step_slug)
            if (not self.current_step or
                    not self.current_step.is_active() or
                    not self.current_step.is_accessible()):
                for step in reversed(self.workflow.steps.values()):
                    if step.is_accessible() and step.is_active():
                        return HttpResponseRedirect(self._reverse(step.view_name))
        return super(WorkflowMixin, self).dispatch(request, *args, **kwargs)

    def get_workflow_class(self):
        return self.workflow_class

    def get_workflow_kwargs(self):
        return {}

    def get_workflow(self):
        return self.get_workflow_class()(**self.get_workflow_kwargs())

    def get_success_url(self):
        if self.current_step.errors:
            view_name = self.current_step.view_name
        else:
            view_name = self.current_step.next_step.view_name
        return self._reverse(view_name)

    def get_context_data(self, **kwargs):
        context = super(WorkflowMixin, self).get_context_data(**kwargs)
        context.update({
            'workflow': self.workflow,
            'current_step': self.current_step,
            'next_step': self.current_step.next_step if self.current_step else None,
        })
        return context


class FinanceTable(object):

    def __init__(self, event, transactions):
        self.event = event
        self.transactions = transactions

    def headers(self):
        return [
            'Timestamp (%s)' % self.event.timezone,
            'Created By',
            'Method',
            'Type',
            'Order',
            'Amount',
            'Dancerfly Fee',
            'Payment Fee',
        ]

    def header_cells(self):
        return [Cell(field='header', value=col) for col in self.headers()]

    def get_rows(self, include_headers=False):
        if include_headers:
            yield self.header_cells()
        for transaction in self.transactions:
            yield self.format_transaction(transaction)

    def money(self, amount):
        return format_money(amount, self.event.currency)

    def format_transaction(self, transaction):
        return Row((
            ('timestamp', self.format_timestamp(transaction)),
            ('created_by', self.created_by_name(transaction)),
            ('method', transaction.get_method_display()),
            ('type', transaction.get_transaction_type_display()),
            ('order', self.order_code(transaction)),
            ('amount', self.money(transaction.amount)),
            ('application_fee', self.money(transaction.application_fee)),
            ('processing_fee', self.money(transaction.processing_fee)),
        ), obj=transaction)

    def format_timestamp(self, transaction):
        tz = pytz.timezone(self.event.timezone)
        localtime = timezone.localtime(transaction.timestamp, timezone=tz)
        return localtime.strftime("%B %d, %Y %H:%M:%S")

    def order_code(self, transaction):
        if transaction.order:
            return transaction.order.code
        else:
            return ''

    def created_by_name(self, transaction):
        if transaction.created_by:
            return transaction.created_by.get_full_name()
        else:
            return ''
