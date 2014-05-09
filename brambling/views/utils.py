from functools import wraps

from django.core.urlresolvers import reverse
from django.db.models import Max, Min
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404

from brambling.models import Event


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
    def __init__(self, request, url, label, disabled=False):
        self.request = request
        self.url = url
        self.label = label
        self.disabled = disabled

    def is_active(self):
        return self.request.path.startswith(self.url)


def get_event_nav(event, request):
    cart = request.user.get_cart(event)
    items = (
        ('brambling_event_shop', 'Shop', False),
        ('brambling_event_finalize', 'Finalize cart', not cart),
        ('brambling_event_checkout', 'Checkout', False),
    )
    return [NavItem(request=request, label=label, disabled=disabled,
                    url=reverse(view_name, kwargs={'slug': event.slug}))
            for view_name, label, disabled in items]


def get_event_admin_nav(event, request):
    if not event.editable_by(request.user):
        return []
    items = (
        ('brambling_event_update', 'Edit', {'slug': event.slug}),
        ('brambling_item_list', 'Items', {'event_slug': event.slug}),
        ('brambling_discount_list', 'Discounts', {'event_slug': event.slug}),
    )
    return [NavItem(request, reverse(view_name, kwargs=kwargs), label)
            for view_name, label, kwargs in items]


def ajax_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.is_ajax():
            raise Http404
        return view(request, *args, **kwargs)
    return wrapped
