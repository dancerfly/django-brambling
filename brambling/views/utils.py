from datetime import timedelta
from functools import wraps

from django.core.urlresolvers import reverse
from django.db.models import Max, Min
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.crypto import get_random_string

from brambling.models import Event, Order, BoughtItem


def get_event_or_404(slug):
    qs = Event.objects.annotate(start_date=Min('dates__date'),
                                end_date=Max('dates__date'))
    return get_object_or_404(qs, slug=slug)


def get_order(event, person=None, code=None):
    order = None
    if code is not None:
        order = Order.objects.get(event=event, code=code)
        if person is not None and order.person != person:
            raise Order.DoesNotExist
    elif person is not None:
        try:
            order = Order.objects.get(event=event, person=person)
        except Order.DoesNotExist:
            pass
    if order is None:
        code = get_random_string(8)
        while Order.objects.filter(event=event, code=code).exists():
            code = get_random_string(8)
        order = Order.objects.create(event=event, person=person, code=code)
    return order


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


def get_event_nav(event, request):
    items = (
        ('brambling_event_shop', 'Shop', 'fa-shopping-cart'),
        ('brambling_event_order_summary', 'Order Summary', 'fa-list-alt'),
    )
    return [NavItem(request=request, label=label, icon=icon,
                    url=reverse(view_name, kwargs={'event_slug': event.slug}))
            for view_name, label, icon in items]


def get_event_admin_nav(event, request):
    if not event.editable_by(request.user):
        return []
    items = (
        ('brambling_event_summary', 'Summary', 'fa-dashboard', {'slug': event.slug}),
        ('brambling_event_update', 'Settings', 'fa-cog', {'slug': event.slug}),
        ('brambling_item_list', 'Items', 'fa-list', {'event_slug': event.slug}),
        ('brambling_discount_list', 'Discounts', 'fa-gift', {'event_slug': event.slug}),
        ('brambling_event_attendees', 'Attendees', 'fa-users', {'event_slug': event.slug}),
        ('brambling_event_orders', 'Orders', 'fa-money', {'event_slug': event.slug}),
    )
    return [NavItem(request, reverse(view_name, kwargs=kwargs), label, icon)
            for view_name, label, icon, kwargs in items]


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
    def __init__(self, *args, **kwargs):
        if 'steps' in kwargs:
            raise ValueError("`steps` can't be passed as a kwarg value.")
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.steps = [step(self, index) for index, step in enumerate(args)]


class Step(object):
    name = None
    url = None

    def __init__(self, workflow, index):
        self.workflow = workflow
        self.index = index

    @property
    def previous_step(self):
        if self.index == 0:
            return None
        return self.workflow.steps[self.index - 1]

    @property
    def next_step(self):
        if self.index == len(self.workflow.steps) - 1:
            return None
        return self.workflow.steps[self.index + 1]

    def is_accessible(self):
        if self.previous_step is None:
            return True
        return self.previous_step.is_completed()

    def is_completed(self):
        if not hasattr(self, '_completed'):
            self._completed = self._is_completed()
        return self.is_accessible() and self._completed

    def _is_completed(self):
        raise NotImplementedError("_is_completed must be implemented by subclasses.")

    def is_valid(self):
        return bool(self.errors)

    @property
    def errors(self):
        if not hasattr(self, '_errors'):
            self._errors = self.get_errors()
        return self._errors

    def get_errors(self):
        return []
