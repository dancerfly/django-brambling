from django.conf.urls import patterns, url, include
from django.templatetags.static import static
from django.views.generic.base import TemplateView, RedirectView

from brambling.forms.user import (
    FloppyAuthenticationForm,
    FloppyPasswordResetForm,
    FloppySetPasswordForm,
)
from brambling.models import Discount
from brambling.views.orders import (
    AddToOrderView,
    RemoveFromOrderView,
    ApplyDiscountView,
    RemoveDiscountView,
    ChooseItemsView,
    AttendeeBasicDataView,
    AttendeesView,
    AttendeeHousingView,
    SurveyDataView,
    HostingView,
    SummaryView,
)
from brambling.views.core import (
    UserDashboardView,
    SplashView,
    InviteAcceptView,
    InviteSendView,
    InviteDeleteView,
)
from brambling.views.organizer import (
    EventCreateView,
    EventSummaryView,
    EventUpdateView,
    StripeConnectView,
    DwollaConnectView,
    RemoveEditorView,
    PublishEventView,
    UnpublishEventView,
    ItemListView,
    item_form,
    DiscountListView,
    discount_form,
    AttendeeFilterView,
    OrderFilterView,
    OrderDetailView,
    RefundView,
)
from brambling.views.user import (
    PersonView,
    HomeView,
    RemoveResidentView,
    SignUpView,
    EmailConfirmView,
    send_confirmation_email_view,
    CreditCardAddView,
    CreditCardDeleteView,
    UserDwollaConnectView,
)
from brambling.views.utils import split_view, route_view, get_event_or_404


urlpatterns = patterns('',
    url(r'^favicon\.ico$', RedirectView.as_view(url=static('brambling/favicon.ico'))),

    url(r'^$',
        split_view(lambda r, *a, **k: r.user.is_authenticated(),
                   UserDashboardView.as_view(),
                   SplashView.as_view()),
        name="brambling_dashboard"),
    url(r'^create/$',
        EventCreateView.as_view(),
        name="brambling_event_create"),
    url(r'^stripe_connect/$',
        StripeConnectView.as_view(),
        name="brambling_stripe_connect"),
    url(r'^dwolla_connect/$',
        DwollaConnectView.as_view(),
        name="brambling_dwolla_connect"),

    url(r'^login/$',
        'django.contrib.auth.views.login',
        {'authentication_form': FloppyAuthenticationForm},
        name='login'),
    url(r'^password_reset/$',
        'django.contrib.auth.views.password_reset',
        {'password_reset_form': FloppyPasswordResetForm},
        name='password_reset'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        'django.contrib.auth.views.password_reset_confirm',
        {'set_password_form': FloppySetPasswordForm},
        name='password_reset_confirm'),
    url(r'^', include('django.contrib.auth.urls')),
    url(r'^signup/$',
        SignUpView.as_view(),
        name="brambling_signup"),
    url(r'^email_confirm/send/$',
        send_confirmation_email_view,
        name="brambling_email_confirm_send"),
    url(r'^email_confirm/(?P<pkb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})$',
        EmailConfirmView.as_view(),
        name="brambling_email_confirm"),
    url(r'^invite/(?P<code>[a-zA-Z0-9~-]{20})/$',
        InviteAcceptView.as_view(),
        name="brambling_invite_accept"),
    url(r'^invite/(?P<code>[a-zA-Z0-9~-]{20})/send/$',
        InviteSendView.as_view(),
        name="brambling_invite_send"),
    url(r'^invite/(?P<code>[a-zA-Z0-9~-]{20})/delete/$',
        InviteDeleteView.as_view(),
        name="brambling_invite_delete"),

    url(r'^profile/$',
        PersonView.as_view(),
        name="brambling_user_profile"),
    url(r'^profile/card/add/$',
        CreditCardAddView.as_view(),
        name="brambling_user_card_add"),
    url(r'^profile/card/delete/(?P<pk>\d+)/$',
        CreditCardDeleteView.as_view(),
        name="brambling_user_card_delete"),
    url(r'^profile/dwolla_connect/$',
        UserDwollaConnectView.as_view(),
        name="brambling_user_dwolla_connect"),
    url(r'^home/$',
        HomeView.as_view(),
        name="brambling_home"),
    url(r'^home/remove_resident/(?P<pk>\d+)/$',
        RemoveResidentView.as_view(),
        name='brambling_home_remove_resident'),

    url(r'^daguerre/', include('daguerre.urls')),

    url(r'^(?P<event_slug>[\w-]+)/$',
        RedirectView.as_view(pattern_name="brambling_event_order_summary", permanent=False),
        name="brambling_event_root"),
    url(r'^(?P<event_slug>[\w-]+)/order/shop/$',
        ChooseItemsView.as_view(),
        name="brambling_event_shop"),
    url(r'^(?P<event_slug>[\w-]+)/order/add/(?P<pk>\d+)/$',
        AddToOrderView.as_view(),
        name="brambling_event_shop_add"),
    url(r'^(?P<event_slug>[\w-]+)/order/remove/(?P<pk>\d+)/$',
        RemoveFromOrderView.as_view(),
        name="brambling_event_shop_remove"),

    url(r'^(?P<event_slug>[\w-]+)/order/attendees/$',
        AttendeesView.as_view(),
        name="brambling_event_attendee_list"),
    url(r'^(?P<event_slug>[\w-]+)/order/attendees/(?P<pk>\d+)/$',
        AttendeeBasicDataView.as_view(),
        name="brambling_event_attendee_edit"),

    url(r'^(?P<event_slug>[\w-]+)/order/housing_data/$',
        AttendeeHousingView.as_view(),
        name='brambling_event_attendee_housing'),
    url(r'^(?P<event_slug>[\w-]+)/order/survey/$',
        SurveyDataView.as_view(),
        name='brambling_event_survey'),
    url(r'^(?P<event_slug>[\w-]+)/order/hosting/$',
        HostingView.as_view(),
        name='brambling_event_hosting'),
    url(r'^(?P<event_slug>[\w-]+)/order/summary/$',
        SummaryView.as_view(),
        name="brambling_event_order_summary"),
    url(r'^(?P<event_slug>[\w-]+)/order/discount/use/(?P<discount>{})/$'.format(Discount.CODE_REGEX),
        ApplyDiscountView.as_view(),
        name="brambling_event_use_discount"),

    url(r'^(?P<slug>[\w-]+)/summary/$',
        EventSummaryView.as_view(),
        name="brambling_event_summary"),
    url(r'^(?P<slug>[\w-]+)/edit/$',
        EventUpdateView.as_view(),
        name="brambling_event_update"),
    url(r'^(?P<event_slug>[\w-]+)/remove_editor/(?P<pk>\d+)$',
        RemoveEditorView.as_view(),
        name="brambling_event_remove_editor"),
    url(r'^(?P<event_slug>[\w-]+)/publish/$',
        PublishEventView.as_view(),
        name="brambling_event_publish"),
    url(r'^(?P<event_slug>[\w-]+)/unpublish/$',
        UnpublishEventView.as_view(),
        name="brambling_event_unpublish"),
    url(r'^(?P<event_slug>[\w-]+)/items/$',
        ItemListView.as_view(),
        name="brambling_item_list"),
    url(r'^(?P<event_slug>[\w-]+)/items/create/$',
        item_form,
        name="brambling_item_create"),
    url(r'^(?P<event_slug>[\w-]+)/items/(?P<pk>\d+)/$',
        item_form,
        name="brambling_item_update"),
    url(r'^(?P<event_slug>[\w-]+)/attendees/$',
        AttendeeFilterView.as_view(),
        name="brambling_event_attendees"),
    url(r'^(?P<event_slug>[\w-]+)/orders/$',
        OrderFilterView.as_view(),
        name="brambling_event_orders"),
    url(r'^(?P<event_slug>[\w-]+)/orders/(?P<code>[a-zA-Z0-9]{8})/$',
        OrderDetailView.as_view(),
        name="brambling_event_order_detail"),
    url(r'^(?P<event_slug>[\w-]+)/orders/(?P<code>[a-zA-Z0-9]{8})/remove_discount/(?P<discount_pk>\d+)/$',
        RemoveDiscountView.as_view(),
        name="brambling_event_remove_discount"),
    url(r'^(?P<event_slug>[\w-]+)/orders/(?P<code>[a-zA-Z0-9]{8})/apply_discount/$',
        ApplyDiscountView.as_view(),
        name="brambling_event_apply_discount"),
    url(r'^(?P<event_slug>[\w-]+)/orders/(?P<code>[a-zA-Z0-9]{8})/refund/(?P<item_pk>\d+)/$',
        RefundView.as_view(),
        name="brambling_event_refund"),

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
