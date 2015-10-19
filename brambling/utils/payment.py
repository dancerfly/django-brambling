import datetime
from decimal import Decimal, ROUND_DOWN
import urllib

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils import timezone
from dwolla import constants, transactions, oauth, fundingsources
import stripe

TEST = 'test'
LIVE = 'live'

stripe.api_version = '2015-01-11'
constants.debug = settings.DEBUG


def get_fee(event, amount):
    fee = event.application_fee_percent / 100 * Decimal(str(amount))
    return fee.quantize(Decimal('0.01'), rounding=ROUND_DOWN)


def dwolla_prep(api_type):
    if api_type == LIVE:
        constants.sandbox = False
        constants.client_id = settings.DWOLLA_APPLICATION_KEY
        constants.client_secret = settings.DWOLLA_APPLICATION_SECRET
    else:
        constants.sandbox = True
        constants.client_id = settings.DWOLLA_TEST_APPLICATION_KEY
        constants.client_secret = settings.DWOLLA_TEST_APPLICATION_SECRET


def dwolla_set_tokens(dwolla_obj, api_type, data):
    if 'access_token' not in data:
        if 'error_description' in data:
            raise ValueError(data['error_description'])
        else:
            raise ValueError('Unknown error during token setting.')
    expires = timezone.now() + datetime.timedelta(seconds=data['expires_in'])
    refresh_expires = timezone.now() + datetime.timedelta(seconds=data['refresh_expires_in'])

    if api_type == LIVE:
        dwolla_obj.dwolla_access_token = data['access_token']
        dwolla_obj.dwolla_access_token_expires = expires
        dwolla_obj.dwolla_refresh_token = data['refresh_token']
        dwolla_obj.dwolla_refresh_token_expires = refresh_expires
    else:
        dwolla_obj.dwolla_test_access_token = data['access_token']
        dwolla_obj.dwolla_test_access_token_expires = expires
        dwolla_obj.dwolla_test_refresh_token = data['refresh_token']
        dwolla_obj.dwolla_test_refresh_token_expires = refresh_expires


def dwolla_get_token(dwolla_obj, api_type):
    """
    Gets a working dwolla access token for the correct api,
    refreshing if necessary.
    """
    if api_type == LIVE:
        expires = dwolla_obj.dwolla_access_token_expires
        refresh_expires = dwolla_obj.dwolla_refresh_token_expires
    else:
        expires = dwolla_obj.dwolla_test_access_token_expires
        refresh_expires = dwolla_obj.dwolla_test_refresh_token_expires
    if expires is None or refresh_expires is None:
        raise ValueError("Invalid dwolla object - unknown token expiration.")
    now = timezone.now()
    if expires < now:
        if refresh_expires < now:
            dwolla_obj.clear_dwolla_data(api_type)
            dwolla_obj.save()
            raise ValueError("Token is expired and can't be refreshed.")
        if api_type == LIVE:
            refresh_token = dwolla_obj.dwolla_refresh_token
        else:
            refresh_token = dwolla_obj.dwolla_test_refresh_token
        oauth_data = oauth.refresh(refresh_token)
        dwolla_set_tokens(dwolla_obj, api_type, oauth_data)
        dwolla_obj.save()
    if api_type == LIVE:
        access_token = dwolla_obj.dwolla_access_token
    else:
        access_token = dwolla_obj.dwolla_test_access_token
    return access_token


def dwolla_update_tokens(days):
    """
    Refreshes or clears all tokens that will not be refreshable within the next <days> days.
    """
    end = timezone.now() + datetime.timedelta(days=days)
    count = 0
    cleared_count = 0
    test_count = 0
    cleared_test_count = 0
    from brambling.models import Organization, Person, Order
    for api_type in (LIVE, TEST):
        dwolla_prep(api_type)
        if api_type == LIVE:
            field = 'dwolla_refresh_token'
        else:
            field = 'dwolla_test_refresh_token'
        kwargs = {
            field + '_expires__lt': end,
        }
        for model in (Organization, Person, Order):
            qs = model.objects.filter(**kwargs)
            for item in qs:
                refresh_token = getattr(item, field)
                oauth_data = oauth.refresh(refresh_token)
                try:
                    dwolla_set_tokens(item, api_type, oauth_data)
                except ValueError:
                    item.clear_dwolla_data(api_type)
                    if api_type == LIVE:
                        cleared_count += 1
                    else:
                        cleared_test_count += 1
                else:
                    if api_type == LIVE:
                        count += 1
                    else:
                        test_count += 1
                item.save()
    return count, cleared_count, test_count, cleared_test_count


def dwolla_get_sources(user_or_order, event):
    dwolla_prep(event.api_type)
    access_token = dwolla_get_token(user_or_order, event.api_type)
    if event.api_type == LIVE:
        destination = event.organization.dwolla_user_id
    else:
        destination = event.organization.dwolla_test_user_id
    return fundingsources.get(
        alternate_token=access_token,
        params={
            'destinationid': destination,
            'verified': True
        }
    )


def dwolla_charge(sender, amount, order, event, pin, source):
    """
    Charges to dwolla and returns a charge transaction.
    """
    dwolla_prep(event.api_type)
    access_token = dwolla_get_token(sender, event.api_type)
    organization_access_token = dwolla_get_token(event.organization, event.api_type)
    if event.api_type == LIVE:
        destination = event.organization.dwolla_user_id
    else:
        destination = event.organization.dwolla_test_user_id

    user_charge_id = transactions.send(
        destinationid=destination,
        amount=amount,
        alternate_token=access_token,
        alternate_pin=pin,
        params={
            'facilitatorAmount': float(get_fee(event, amount)),
            'fundsSource': source,
            'notes': "Order {} for {}".format(order.code, event.name),
        },
    )
    # Charge id returned by send_funds is the transaction ID
    # for the user; the event has a different transaction ID.
    # But we can use this one to get that one.

    event_charge = transactions.info(
        tid=str(user_charge_id),
        alternate_token=organization_access_token
    )

    return event_charge


def dwolla_refund(order, event, payment_id, amount, pin):
    """
    Returns id of refund transaction.
    """
    dwolla_prep(event.api_type)
    access_token = dwolla_get_token(event.organization, event.api_type)
    return transactions.refund(
        tid=int(payment_id),
        fundingsource="Balance",
        amount="%.2f" % amount,
        alternate_token=access_token,
        alternate_pin=int(pin),
        params={
            'notes': "Order {} for {}".format(order.code, event.name),
        },
    )


def dwolla_test_settings_valid():
    return bool(
        getattr(settings, 'DWOLLA_TEST_APPLICATION_KEY', False) and
        getattr(settings, 'DWOLLA_TEST_APPLICATION_SECRET', False)
    )


def dwolla_live_settings_valid():
    return bool(
        getattr(settings, 'DWOLLA_APPLICATION_KEY', False) and
        getattr(settings, 'DWOLLA_APPLICATION_SECRET', False)
    )


def dwolla_customer_redirect_url(user_or_order, api_type, request, next_url=""):
    redirect_url = "{}?api={}&type={}&id={}".format(
        reverse('brambling_dwolla_connect'),
        api_type,
        user_or_order._meta.model_name,
        user_or_order.pk,
    )
    if next_url:
        redirect_url += "&next_url=" + next_url
    return request.build_absolute_uri(redirect_url)


def dwolla_customer_oauth_url(user_or_order, api_type, request, next_url=""):
    dwolla_prep(api_type)
    scope = "Send|AccountInfoFull|Funding"
    return oauth.genauthurl(
        dwolla_customer_redirect_url(
            user_or_order,
            api_type,
            request,
            next_url,
        ),
        scope=scope,
    )


def dwolla_organization_redirect_url(organization, request, api_type):
    redirect_url = "{}?api={}&type={}&id={}".format(
        reverse('brambling_dwolla_connect'),
        api_type,
        organization._meta.model_name,
        organization.pk,
    )
    return request.build_absolute_uri(redirect_url)


def dwolla_organization_oauth_url(organization, request, api_type):
    dwolla_prep(api_type)
    scope = "Send|AccountInfoFull|Transactions"
    return oauth.genauthurl(
        dwolla_organization_redirect_url(
            organization,
            request,
            api_type,
        ),
        scope=scope,
    )


def stripe_prep(api_type):
    if api_type == LIVE:
        stripe.api_key = settings.STRIPE_SECRET_KEY
    else:
        stripe.api_key = settings.STRIPE_TEST_SECRET_KEY


def stripe_charge(card_or_token, amount, order, event, customer=None):
    if amount <= 0:
        return None
    stripe_prep(event.api_type)
    if event.api_type == LIVE:
        access_token = event.organization.stripe_access_token
    else:
        access_token = event.organization.stripe_test_access_token
    stripe.api_key = access_token

    if customer is not None:
        card_or_token = stripe.Token.create(
            customer=customer,
            card=card_or_token,
            api_key=access_token,
        )
    return stripe.Charge.create(
        amount=int(amount * 100),
        currency=event.currency,
        card=card_or_token,
        application_fee=int(get_fee(event, amount) * 100),
        expand=['balance_transaction'],
        metadata={
            'order': order.code,
            'event': event.name,
        },
    )


def stripe_refund(order, event, payment_id, amount):
    stripe_prep(event.api_type)
    if event.api_type == LIVE:
        access_token = event.organization.stripe_access_token
    else:
        access_token = event.organization.stripe_test_access_token
    stripe.api_key = access_token
    # Retrieving the charge and refunding it uses the access token.
    charge = stripe.Charge.retrieve(payment_id)
    refund = charge.refunds.create(
        amount=int(amount*100),
        refund_application_fee=True,
        expand=['balance_transaction'],
        metadata={
            'order': order.code,
            'event': event.name,
        },
    )

    # Retrieving the application fee data requires the application api token.
    stripe_prep(event.api_type)
    try:
        application_fee = stripe.ApplicationFee.all(charge=charge).data[0]
        application_fee_refund = application_fee.refunds.data[0]
    except IndexError:
        raise Exception("No application fee refund found.")
    return {
        'refund': refund,
        'application_fee_refund': application_fee_refund,
    }


def stripe_test_settings_valid():
    return bool(
        getattr(settings, 'STRIPE_TEST_APPLICATION_ID', False) and
        getattr(settings, 'STRIPE_TEST_SECRET_KEY', False) and
        getattr(settings, 'STRIPE_TEST_PUBLISHABLE_KEY', False)
    )


def stripe_live_settings_valid():
    return bool(
        getattr(settings, 'STRIPE_APPLICATION_ID', False) and
        getattr(settings, 'STRIPE_SECRET_KEY', False) and
        getattr(settings, 'STRIPE_PUBLISHABLE_KEY', False)
    )


def stripe_organization_oauth_url(organization, request, api_type):
    stripe_prep(api_type)
    if api_type == LIVE:
        client_id = getattr(settings, 'STRIPE_APPLICATION_ID', None)
    else:
        client_id = getattr(settings, 'STRIPE_TEST_APPLICATION_ID', None)
    if not client_id:
        return ''
    redirect_uri = request.build_absolute_uri(reverse('brambling_stripe_connect'))
    base_url = "https://connect.stripe.com/oauth/authorize?client_id={client_id}&response_type=code&scope=read_write&state={state}&redirect_uri={redirect_uri}"
    return base_url.format(client_id=client_id,
                           state="{}|{}".format(organization.slug, api_type),
                           redirect_uri=urllib.quote(redirect_uri))
