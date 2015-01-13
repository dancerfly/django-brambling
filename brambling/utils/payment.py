from django.conf import settings
from dwolla import constants, transactions, oauth
import stripe

TEST = 'test'
LIVE = 'live'

stripe.api_version = '2015-01-11'
constants.debug = settings.DEBUG


def dwolla_prep(api_type):
    if api_type == LIVE:
        constants.sandbox = False
        constants.client_id = settings.DWOLLA_APPLICATION_KEY
        constants.client_secret = settings.DWOLLA_APPLICATION_SECRET
    else:
        constants.sandbox = True
        constants.client_id = settings.DWOLLA_TEST_APPLICATION_KEY
        constants.client_secret = settings.DWOLLA_TEST_APPLICATION_SECRET


def dwolla_charge(user_or_order, amount, event, pin, fee):
    """
    Charges to dwolla and returns a charge id.
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
        params={'facil_amount': fee}
    )
    # Charge id returned by send_funds is the transaction ID
    # for the user; the event has a different transaction ID.
    # But we can use this one to get that one.

    event_charge = transactions.info(
        tid=user_charge_id,
        alternate_token=event_access_token
    )

    return event_charge['Id']


def dwolla_refund(event, payment_id, amount, pin):
    """
    Returns id of refund transaction.
    """
    dwolla_prep(event.api_type)
    if event.api_type == LIVE:
        access_token = event.dwolla_access_token
    else:
        access_token = event.dwolla_test_access_token
    refund = transactions.refund(
        tid=payment_id,
        fundingsource="Balance",
        amount=amount,
        alternate_token=access_token,
        alternate_pin=pin
    )
    return refund['TransactionId']


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
        redirect_url += "&next_url" + next_url
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
