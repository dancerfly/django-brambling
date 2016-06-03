from dwolla import transactions, fundingsources

from brambling.payment.core import InvalidAmountException, get_fee
from brambling.payment.dwolla.core import dwolla_prep


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
