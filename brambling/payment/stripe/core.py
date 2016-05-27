from django.conf import settings
import stripe

from brambling.payment.core import LIVE


def stripe_prep(api_type):
    stripe.api_version = '2015-01-11'
    if api_type == LIVE:
        stripe.api_key = settings.STRIPE_SECRET_KEY
    else:
        stripe.api_key = settings.STRIPE_TEST_SECRET_KEY


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
