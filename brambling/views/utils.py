from datetime import timedelta
from functools import wraps

from django.core.urlresolvers import reverse
from django.db.models import Max, Min
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone

from brambling.models import Event, EventPerson, BoughtItem


def get_event_or_404(slug):
    qs = Event.objects.annotate(start_date=Min('dates__date'),
                                end_date=Max('dates__date'))
    return get_object_or_404(qs, slug=slug)


def get_event_person(event, person):
    event_person = EventPerson.objects.get_or_create(event=event, person=person)[0]
    event_person.event = event
    event_person.person = person
    return event_person


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
        ('brambling_event_records', 'Records', 'fa-list-alt'),
    )
    return [NavItem(request=request, label=label, icon=icon,
                    url=reverse(view_name, kwargs={'event_slug': event.slug}))
            for view_name, label, icon in items]


def get_event_admin_nav(event, request):
    if not event.editable_by(request.user):
        return []
    items = (
        ('brambling_event_dashboard', 'Dashboard', 'fa-dashboard', {'slug': event.slug}),
        ('brambling_event_update', 'Settings', 'fa-cog', {'slug': event.slug}),
        ('brambling_item_list', 'Items', 'fa-list', {'event_slug': event.slug}),
        ('brambling_discount_list', 'Discounts', 'fa-gift', {'event_slug': event.slug}),
        ('brambling_event_attendees', 'Attendees', 'fa-users', {'event_slug': event.slug}),
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
        event_person__event=event,
        event_person__cart_start_time__isnull=False,
        event_person__cart_start_time__lte=expired_before
    ).delete()
