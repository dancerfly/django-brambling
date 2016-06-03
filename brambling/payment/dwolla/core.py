from django.conf import settings
from dwolla import constants

from brambling.payment.core import LIVE


def dwolla_prep(api_type):
    constants.debug = settings.DEBUG
    if api_type == LIVE:
        constants.sandbox = False
        constants.client_id = settings.DWOLLA_APPLICATION_KEY
        constants.client_secret = settings.DWOLLA_APPLICATION_SECRET
    else:
        constants.sandbox = True
        constants.client_id = settings.DWOLLA_TEST_APPLICATION_KEY
        constants.client_secret = settings.DWOLLA_TEST_APPLICATION_SECRET


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
