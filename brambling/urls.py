from django.conf.urls import patterns, url, include

from brambling.views import (EventDetailView, EventCreateView,
                             EventUpdateView, PersonView, HouseView,
                             ItemListView, item_form, DiscountListView,
                             discount_form)


urlpatterns = patterns('',
    url(r'^$',
        "brambling.views.home",
        name="home"),
    url(r'^create/$',
        EventCreateView.as_view(),
        name="brambling_event_create"),

    url(r'^', include('django.contrib.auth.urls')),

    url(r'^profile/$',
        PersonView.as_view(),
        name="brambling_user_profile"),
    url(r'^house/$',
        HouseView.as_view(),
        name="brambling_house"),

    url(r'^(?P<slug>[\w-]+)/$',
        EventDetailView.as_view(),
        name="brambling_event_detail"),
    url(r'^(?P<slug>[\w-]+)/edit/$',
        EventUpdateView.as_view(),
        name="brambling_event_update"),

    url(r'^(?P<event_slug>[\w-]+)/items/$',
        ItemListView.as_view(),
        name="brambling_item_list"),
    url(r'^(?P<event_slug>[\w-]+)/items/create/$',
        item_form,
        name="brambling_item_create"),
    url(r'^(?P<event_slug>[\w-]+)/items/(?P<pk>\d+)/$',
        item_form,
        name="brambling_item_update"),

    url(r'^(?P<event_slug>[\w-]+)/discount/$',
        DiscountListView.as_view(),
        name="brambling_discount_list"),
    url(r'^(?P<event_slug>[\w-]+)/discount/create/$',
        discount_form,
        name="brambling_discount_create"),
    url(r'^(?P<event_slug>[\w-]+)/discount/(?P<pk>\d+)/$',
        discount_form,
        name="brambling_discount_update"),
)
