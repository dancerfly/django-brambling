from datetime import timedelta, datetime

from django.utils.timezone import now
import factory
import pytz

from brambling.models import (Event, Person, Order, CreditCard, Invite,
                              Organization, Transaction)


def lazy_setting(setting):
    def wrapped(obj):
        from django.conf import settings
        return getattr(settings, setting)
    return wrapped


class CardFactory(factory.DjangoModelFactory):
    class Meta:
        model = CreditCard

    stripe_card_id = 'FAKE_CARD'
    api_type = Event.TEST
    exp_month = 11
    exp_year = 99
    fingerprint = 'FAKE_FINGERPRINT'
    last4 = '4242'
    brand = 'Visa'


class PersonFactory(factory.DjangoModelFactory):
    class Meta:
        model = Person

    given_name = factory.Sequence(lambda n: "User{}".format(n))
    surname = "Test"

    email = factory.Sequence(lambda n: "test{}@test.com".format(n))
    confirmed_email = factory.LazyAttribute(lambda obj: obj.email)

    dwolla_test_user_id = factory.LazyAttribute(lazy_setting('DWOLLA_TEST_USER_USER_ID'))
    dwolla_test_access_token = factory.LazyAttribute(lazy_setting('DWOLLA_TEST_USER_ACCESS_TOKEN'))
    dwolla_test_refresh_token = factory.LazyAttribute(lazy_setting('DWOLLA_TEST_USER_REFRESH_TOKEN'))
    dwolla_test_access_token_expires = datetime(2015, 5, 23, 22, 29, 24, 745430, tzinfo=pytz.utc)
    dwolla_test_refresh_token_expires = datetime(2015, 7, 22, 21, 29, 24, 745452, tzinfo=pytz.utc)


class OrganizationFactory(factory.DjangoModelFactory):
    class Meta:
        model = Organization

    name = "Test organization"
    slug = factory.Sequence(lambda n: "test-event-{}".format(n))
    owner = factory.SubFactory(PersonFactory)

    stripe_test_access_token = factory.LazyAttribute(lazy_setting('STRIPE_TEST_ORGANIZATION_ACCESS_TOKEN'))
    stripe_test_publishable_key = factory.LazyAttribute(lazy_setting('STRIPE_TEST_ORGANIZATION_PUBLISHABLE_KEY'))
    stripe_test_refresh_token = factory.LazyAttribute(lazy_setting('STRIPE_TEST_ORGANIZATION_REFRESH_TOKEN'))
    stripe_test_user_id = factory.LazyAttribute(lazy_setting('STRIPE_TEST_ORGANIZATION_USER_ID'))

    dwolla_test_user_id = factory.LazyAttribute(lazy_setting('DWOLLA_TEST_ORGANIZATION_USER_ID'))
    dwolla_test_access_token = factory.LazyAttribute(lazy_setting('DWOLLA_TEST_ORGANIZATION_ACCESS_TOKEN'))
    dwolla_test_refresh_token = factory.LazyAttribute(lazy_setting('DWOLLA_TEST_ORGANIZATION_REFRESH_TOKEN'))
    dwolla_test_access_token_expires = datetime(2015, 5, 23, 22, 22, 27, 144345, tzinfo=pytz.utc)
    dwolla_test_refresh_token_expires = datetime(2015, 7, 22, 21, 22, 27, 144376, tzinfo=pytz.utc)


class EventFactory(factory.DjangoModelFactory):
    class Meta:
        model = Event

    name = "Test event"
    slug = factory.Sequence(lambda n: "test-event-{}".format(n))
    city = "Test City"
    state_or_province = "SOP"
    api_type = Event.TEST
    organization = factory.SubFactory(OrganizationFactory)
    start_date = now().date() + timedelta(days=2)
    end_date = now().date() + timedelta(days=3)


class OrderFactory(factory.DjangoModelFactory):
    class Meta:
        model = Order

    code = factory.Sequence(lambda n: str(n).zfill(6))
    event = factory.SubFactory(EventFactory)
    dwolla_test_user_id = factory.LazyAttribute(lazy_setting('DWOLLA_TEST_USER_USER_ID'))
    dwolla_test_access_token = factory.LazyAttribute(lazy_setting('DWOLLA_TEST_USER_ACCESS_TOKEN'))


class InviteFactory(factory.DjangoModelFactory):
    class Meta:
        model = Invite

    code = factory.Sequence(lambda n: "invite{}".format(n))
    email = "test@test.com"
    user = factory.SubFactory(PersonFactory)
    kind = Invite.EVENT_EDITOR


class TransactionFactory(factory.DjangoModelFactory):
    class Meta:
        model = Transaction

    event = factory.SubFactory(EventFactory)
