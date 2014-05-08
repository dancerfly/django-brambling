from django.db.models import Max, Min
from django.shortcuts import get_object_or_404
from brambling.models import Event


def get_event_or_404(slug):
    qs = Event.objects.annotate(start_date=Min('dates__date'),
                                end_date=Max('dates__date'))
    return get_object_or_404(qs, slug=slug)


def split_view(test, if_true, if_false):
    def wrapped(request, *args, **kwargs):
        view = if_true if test(request) else if_false
        return view(request, *args, **kwargs)
    return wrapped
