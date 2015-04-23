from collections import OrderedDict
from datetime import timedelta
from functools import wraps
from itertools import ifilter

from django.core.urlresolvers import reverse
from django.db.models import Max, Min
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone

from brambling.models import Event, BoughtItem


def get_event_or_404(slug):
    qs = Event.objects.annotate(start_date=Min('dates__date'),
                                end_date=Max('dates__date'))
    return get_object_or_404(qs, slug=slug)


def split_view(test, if_true, if_false):
    # Renders if_true view if condition is true, else if_false
    def wrapped(request, *args, **kwargs):
        view = if_true if test(request, *args, **kwargs) else if_false
        return view(request, *args, **kwargs)
    return wrapped


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
    kwargs = {
        'event_slug': event.slug,
        'organization_slug': event.organization.slug,
    }
    items = (
        ('brambling_event_summary', 'Summary', 'fa-dashboard'),
        ('brambling_event_update', 'Settings', 'fa-cog'),
        ('brambling_item_list', 'Items', 'fa-list'),
        ('brambling_form_list', 'Forms', 'fa-question'),
        ('brambling_discount_list', 'Discounts', 'fa-gift'),
        ('brambling_event_attendees', 'Attendees', 'fa-users'),
        ('brambling_event_orders', 'Orders', 'fa-ticket'),
        ('brambling_event_finances', 'Finances', 'fa-money'),
    )
    return [NavItem(request, reverse(view_name, kwargs=kwargs), label, icon)
            for view_name, label, icon in items]


def get_organization_admin_nav(organization, request):
    kwargs = {
        'organization_slug': organization.slug,
    }
    items = (
        ('brambling_organization_update', 'Profile'),
        ('brambling_organization_update_payment', 'Payment'),
        ('brambling_organization_update_event_defaults', 'Event Defaults'),
        ('brambling_organization_update_permissions', 'Permissions'),
    )
    return [NavItem(request, reverse(view_name, kwargs=kwargs), label, None)
            for view_name, label in items]


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
