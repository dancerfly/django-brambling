from decimal import Decimal, ROUND_DOWN
import urllib

from django.conf import settings
from django.core.urlresolvers import reverse
from dwolla import constants, transactions, oauth
import stripe

TEST = 'test'
LIVE = 'live'

stripe.api_version = '2015-01-11'
constants.debug = settings.DEBUG


def get_fee(event, amount):
    fee = Decimal(event.application_fee_percent / 100 * amount)
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


def dwolla_charge(user_or_order, amount, event, pin):
    """
    Charges to dwolla and returns a charge transaction.
    """
    dwolla_prep(event.api_type)
    if event.api_type == LIVE:
        access_token = user_or_order.dwolla_access_token
        destination = event.dwolla_user_id
        event_access_token = event.dwolla_access_token
    else:
        access_token = user_or_order.dwolla_test_access_token
        destination = event.dwolla_test_user_id
        event_access_token = event.dwolla_test_access_token

    user_charge_id = transactions.send(
        destinationid=destination,
        amount=amount,
        alternate_token=access_token,
        alternate_pin=pin,
        params={'facilitatorAmount': float(get_fee(event, amount))}
    )
    # Charge id returned by send_funds is the transaction ID
    # for the user; the event has a different transaction ID.
    # But we can use this one to get that one.

    event_charge = transactions.info(
        tid=str(user_charge_id),
        alternate_token=event_access_token
    )

    return event_charge


def dwolla_refund(event, payment_id, amount, pin):
    """
    Returns id of refund transaction.
    """
    dwolla_prep(event.api_type)
    if event.api_type == LIVE:
        access_token = event.dwolla_access_token
    else:
        access_token = event.dwolla_test_access_token
    return transactions.refund(
        tid=int(payment_id),
        fundingsource="Balance",
        amount="%.2f" % amount,
        alternate_token=access_token,
        alternate_pin=int(pin)
    )


def dwolla_can_connect(obj, api_type):
    if api_type == LIVE:
        return bool(
            getattr(settings, 'DWOLLA_APPLICATION_KEY', False) and
            getattr(settings, 'DWOLLA_APPLICATION_SECRET', False) and
            not obj.dwolla_user_id
        )
    return bool(
        getattr(settings, 'DWOLLA_TEST_APPLICATION_KEY', False) and
        getattr(settings, 'DWOLLA_TEST_APPLICATION_SECRET', False) and
        not obj.dwolla_test_user_id
    )


def dwolla_is_connected(obj, api_type):
    if api_type == LIVE:
        return bool(
            obj.dwolla_user_id and
            getattr(settings, 'DWOLLA_APPLICATION_KEY', False) and
            getattr(settings, 'DWOLLA_APPLICATION_SECRET', False)
        )
    return bool(
        obj.dwolla_test_user_id and
        getattr(settings, 'DWOLLA_TEST_APPLICATION_KEY', False) and
        getattr(settings, 'DWOLLA_TEST_APPLICATION_SECRET', False)
    )


def dwolla_customer_oauth_url(user_or_order, api_type, request, next_url=""):
    dwolla_prep(api_type)
    scope = "Send|AccountInfoFull"
    redirect_url = user_or_order.get_dwolla_connect_url() + "?api=" + api_type
    if next_url:
        redirect_url += "&next_url=" + next_url
    redirect_url = request.build_absolute_uri(redirect_url)
    return oauth.genauthurl(redirect_url, scope=scope)


def dwolla_event_oauth_url(event, request):
    dwolla_prep(event.api_type)
    scope = "Send|AccountInfoFull|Transactions"
    redirect_url = request.build_absolute_uri(event.get_dwolla_connect_url() + "?api=" + event.api_type)
    return oauth.genauthurl(redirect_url, scope=scope)


def stripe_prep(api_type):
    if api_type == LIVE:
        stripe.api_key = settings.STRIPE_SECRET_KEY
    else:
        stripe.api_key = settings.STRIPE_TEST_SECRET_KEY


def stripe_charge(card_or_token, amount, event, customer=None):
    if amount <= 0:
        return None
    stripe_prep(event.api_type)
    if event.api_type == LIVE:
        access_token = event.stripe_access_token
    else:
        access_token = event.stripe_test_access_token
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
        expand=['balance_transaction']
    )


def stripe_refund(event, payment_id, amount):
    stripe_prep(event.api_type)
    if event.api_type == LIVE:
        access_token = event.stripe_access_token
    else:
        access_token = event.stripe_test_access_token
    stripe.api_key = access_token
    charge = stripe.Charge.retrieve(payment_id)
    refund = charge.refunds.create(
        amount=int(amount*100),
        refund_application_fee=True,
        expand=['balance_transaction'],
    )
    try:
        application_fee = stripe.ApplicationFee.all(charge=charge).data[0]
        application_fee_refund = application_fee.refunds.data[0]
    except IndexError:
        raise Exception("No application fee refund found.")
    return {
        'refund': refund,
        'application_fee_refund': application_fee_refund,
    }


def stripe_can_connect(obj, api_type):
    if api_type == LIVE:
        return bool(
            getattr(settings, 'STRIPE_APPLICATION_ID', False) and
            getattr(settings, 'STRIPE_SECRET_KEY', False) and
            getattr(settings, 'STRIPE_PUBLISHABLE_KEY', False) and
            not obj.stripe_user_id
        )
    return bool(
        getattr(settings, 'STRIPE_TEST_APPLICATION_ID', False) and
        getattr(settings, 'STRIPE_TEST_SECRET_KEY', False) and
        getattr(settings, 'STRIPE_TEST_PUBLISHABLE_KEY', False) and
        not obj.stripe_test_user_id
    )


def stripe_is_connected(obj, api_type):
    if api_type == LIVE:
        return bool(
            obj.stripe_user_id and
            getattr(settings, 'STRIPE_APPLICATION_ID', False) and
            getattr(settings, 'STRIPE_SECRET_KEY', False) and
            getattr(settings, 'STRIPE_PUBLISHABLE_KEY', False)
        )
    return bool(
        obj.stripe_test_user_id and
        getattr(settings, 'STRIPE_TEST_APPLICATION_ID', False) and
        getattr(settings, 'STRIPE_TEST_SECRET_KEY', False) and
        getattr(settings, 'STRIPE_TEST_PUBLISHABLE_KEY', False)
    )


def stripe_event_oauth_url(event, request):
    stripe_prep(event.api_type)
    if event.api_type == LIVE:
        client_id = getattr(settings, 'STRIPE_APPLICATION_ID', None)
    else:
        client_id = getattr(settings, 'STRIPE_TEST_APPLICATION_ID', None)
    if not client_id:
        return ''
    redirect_uri = request.build_absolute_uri(reverse('brambling_stripe_connect'))
    base_url = "https://connect.stripe.com/oauth/authorize?client_id={client_id}&response_type=code&scope=read_write&state={state}&redirect_uri={redirect_uri}"
    return base_url.format(client_id=client_id,
                           state=event.slug,
                           redirect_uri=urllib.quote(redirect_uri))
