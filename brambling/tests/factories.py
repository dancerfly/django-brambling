from datetime import timedelta, datetime

from django.utils.timezone import now
import factory
import pytz

from brambling.models import (Event, Person, Order, CreditCard, Invite,
                              Organization, Transaction, Item, ItemOption,
                              Discount, Attendee)


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
    dwolla_test_access_token_expires = now() + timedelta(days=2)
    dwolla_test_refresh_token_expires = now() + timedelta(days=2)


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
    dwolla_test_access_token_expires = now() - timedelta(days=1)
    dwolla_test_refresh_token_expires = now() + timedelta(days=2)


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


class AttendeeFactory(factory.DjangoModelFactory):
    class Meta:
        model = Attendee

    given_name = factory.Sequence(lambda n: "Attendee{}".format(n))
    surname = "Test"

    email = factory.Sequence(lambda n: "test{}@test.com".format(n))
    order = factory.SubFactory(OrderFactory)

    @factory.post_generation
    def bought_items(self, create, extracted, **kwargs):
        if not create:
            return

        for bought_item in extracted:
            self.bought_items.add(bought_item)


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


class ItemFactory(factory.DjangoModelFactory):
    class Meta:
        model = Item

    name = factory.Sequence(lambda n: "Item {}".format(n))
    event = factory.SubFactory(EventFactory)


class ItemOptionFactory(factory.DjangoModelFactory):
    class Meta:
        model = ItemOption

    name = factory.Sequence(lambda n: "ItemOption {}".format(n))
    item = factory.SubFactory(ItemFactory)
    price = 1
    available_end = now() + timedelta(days=2)
    order = 1


class DiscountFactory(factory.DjangoModelFactory):
    class Meta:
        model = Discount

    name = factory.Sequence(lambda n: "Discount {}".format(n))
    code = factory.Sequence(lambda n: unicode(n))
    available_end = now() + timedelta(days=2)
    amount = 1
    event = factory.SubFactory(EventFactory)

    @factory.post_generation
    def item_options(self, create, extracted, **kwargs):
        if not create:
            return

        if not extracted:
            extracted = [ItemOptionFactory()]

        for item_option in extracted:
            self.item_options.add(item_option)
