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

DWOLLA_SCOPES = "send|accountinfofull|funding|transactions"


class InvalidAmountException(ValueError):
    """The amount to be charged must be zero or positive."""


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


def dwolla_update_tokens(days):
    """
    Refreshes or clears all tokens that will not be refreshable within the next <days> days.
    """
    end = timezone.now() + datetime.timedelta(days=days)
    count = 0
    invalid_count = 0
    test_count = 0
    invalid_test_count = 0
    from brambling.models import DwollaAccount
    accounts = DwollaAccount.objects.filter(
        refresh_token_expires__lt=end,
        is_valid=True,
    )
    for account in accounts:
        refresh_token = account.refresh_token
        dwolla_prep(account.api_type)
        oauth_data = oauth.refresh(refresh_token)
        try:
            account.set_tokens(oauth_data)
        except ValueError:
            account.is_valid = False
            if account.api_type == LIVE:
                invalid_count += 1
            else:
                invalid_test_count += 1
        else:
            if account.api_type == LIVE:
                count += 1
            else:
                test_count += 1
        account.save()
    return count, invalid_count, test_count, invalid_test_count


def dwolla_get_sources(account, event):
    if account.api_type != event.api_type:
        raise ValueError("Account and event API types do not match.")
    org_account = event.organization.get_dwolla_account(event.api_type)
    if not org_account or not org_account.is_connected():
        raise ValueError("Event is not connected to dwolla.")
    dwolla_prep(account.api_type)
    access_token = account.get_token()
    destination = org_account.user_id
    return fundingsources.get(
        alternate_token=access_token,
        params={
            'destinationid': destination,
            'verified': True
        }
    )


def dwolla_charge(account, amount, order, event, pin, source):
    """
    Charges to dwolla and returns a charge transaction.
    """
    if amount < 0:
        raise InvalidAmountException('Cannot charge an amount less than zero.')
    if account.api_type != event.api_type:
        raise ValueError("Account and event API types do not match.")
    org_account = event.organization.get_dwolla_account(event.api_type)
    if not org_account or not org_account.is_connected():
        raise ValueError("Event is not connected to dwolla.")
    dwolla_prep(account.api_type)
    access_token = account.get_token()
    organization_access_token = org_account.get_token()
    destination = org_account.user_id

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
    org_account = event.organization.get_dwolla_account(event.api_type)
    dwolla_prep(event.api_type)
    access_token = org_account.get_token()
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


def dwolla_redirect_url(dwolla_obj, api_type, request, next_url=""):
    redirect_url = "{}?api={}&type={}&id={}".format(
        reverse('brambling_dwolla_connect'),
        api_type,
        dwolla_obj._meta.model_name,
        dwolla_obj.pk,
    )
    if next_url:
        redirect_url += "&next_url=" + next_url
    return request.build_absolute_uri(redirect_url)


def dwolla_oauth_url(dwolla_obj, api_type, request, next_url=""):
    dwolla_prep(api_type)
    redirect_url = dwolla_redirect_url(dwolla_obj, api_type, request, next_url)
    return oauth.genauthurl(redirect_url, scope=DWOLLA_SCOPES)


def stripe_prep(api_type):
    if api_type == LIVE:
        stripe.api_key = settings.STRIPE_SECRET_KEY
    else:
        stripe.api_key = settings.STRIPE_TEST_SECRET_KEY


def stripe_charge(card_or_token, amount, order, event, customer=None):
    if amount < 0:
        raise InvalidAmountException('Cannot charge an amount less than zero.')
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
        amount=int(amount * 100),
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


def stripe_organization_oauth_url(organization, api_type, request):
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
