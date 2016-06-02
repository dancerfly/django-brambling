import stripe

from brambling.payment.core import LIVE, InvalidAmountException, get_fee
from brambling.payment.stripe.core import stripe_prep


def stripe_get_customer(user, api_type, create=True):
    stripe_prep(api_type)

    if api_type == LIVE:
        customer_attr = 'stripe_customer_id'
    else:
        customer_attr = 'stripe_test_customer_id'
    customer_id = getattr(user, customer_attr)

    if not customer_id:
        if not create:
            return None
        customer = stripe.Customer.create(
            email=user.email,
            description=user.get_full_name(),
            metadata={
                'brambling_id': user.id
            },
        )
        setattr(user, customer_attr, customer.id)
        user.save()
    else:
        customer = stripe.Customer.retrieve(customer_id)
    return customer


def stripe_add_card(customer, token, api_type):
    stripe_prep(api_type)
    return customer.sources.create(source=token)


def stripe_delete_card(customer, card_id):
    customer.sources.retrieve(card_id).delete()


def stripe_charge(source, amount, order, event, customer=None):
    if amount < 0:
        raise InvalidAmountException('Cannot charge an amount less than zero.')
    stripe_prep(event.api_type)
    if event.api_type == LIVE:
        stripe_account = event.organization.stripe_user_id
    else:
        stripe_account = event.organization.stripe_test_user_id

    if customer is not None:
        source = stripe.Token.create(
            customer=customer,
            card=source,
            stripe_account=stripe_account,
        )
    return stripe.Charge.create(
        amount=int(amount * 100),
        currency=event.currency,
        source=source,
        application_fee=int(get_fee(event, amount) * 100),
        expand=['balance_transaction'],
        metadata={
            'order': order.code,
            'event': event.name,
        },
        stripe_account=stripe_account,
    )


def stripe_refund(order, event, payment_id, amount):
    stripe_prep(event.api_type)
    if event.api_type == LIVE:
        access_token = event.organization.stripe_access_token
    else:
        access_token = event.organization.stripe_test_access_token
    # Retrieving the charge and refunding it uses the access token.
    stripe.api_key = access_token
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
