import stripe

from brambling.payment.core import LIVE, InvalidAmountException, get_fee
from brambling.payment.stripe.core import stripe_prep


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
