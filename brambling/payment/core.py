from decimal import Decimal, ROUND_DOWN

TEST = 'test'
LIVE = 'live'


class InvalidAmountException(ValueError):
    """The amount to be charged must be zero or positive."""


def get_fee(event, amount):
    fee = event.application_fee_percent / 100 * Decimal(str(amount))
    return fee.quantize(Decimal('0.01'), rounding=ROUND_DOWN)
