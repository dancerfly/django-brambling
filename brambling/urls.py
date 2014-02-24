from django.conf.urls import patterns, url

from brambling.views import (EventListView, EventDetailView, EventCreateView,
                             EventUpdateView)


urlpatterns = patterns('',
    url(r'^$',
        EventListView.as_view(),
        name="brambling_event_list"),
    url(r'^create/$',
        EventCreateView.as_view(),
        name="brambling_event_create"),
    url(r'^(?P<slug>[\w-]+)/$',
        EventDetailView.as_view(),
        name="brambling_event_detail"),
    url(r'^(?P<slug>[\w-]+)/edit/$',
        EventUpdateView.as_view(),
        name="brambling_event_update"),
)
