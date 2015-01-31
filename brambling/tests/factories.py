import factory

from brambling.models import Event, Person, Order


def lazy_setting(setting):
    def wrapped(obj):
        from django.conf import settings
        return getattr(settings, setting)
    return wrapped


class PersonFactory(factory.DjangoModelFactory):
    class Meta:
        model = Person

    email = factory.Sequence(lambda n: "test{}@test.com".format(n))
    confirmed_email = factory.LazyAttribute(lambda obj: obj.email)

    dwolla_test_user_id = factory.LazyAttribute(lazy_setting('DWOLLA_TEST_USER_USER_ID'))
    dwolla_test_access_token = factory.LazyAttribute(lazy_setting('DWOLLA_TEST_USER_ACCESS_TOKEN'))


class EventFactory(factory.DjangoModelFactory):
    class Meta:
        model = Event

    name = "Test event"
    slug = factory.Sequence(lambda n: "test-event-{}".format(n))
    city = "Test City"
    state_or_province = "SOP"
    api_type = Event.TEST
    owner = factory.SubFactory(PersonFactory)

    stripe_test_access_token = factory.LazyAttribute(lazy_setting('STRIPE_TEST_EVENT_ACCESS_TOKEN'))
    stripe_test_publishable_key = factory.LazyAttribute(lazy_setting('STRIPE_TEST_EVENT_PUBLISHABLE_KEY'))
    stripe_test_refresh_token = factory.LazyAttribute(lazy_setting('STRIPE_TEST_EVENT_REFRESH_TOKEN'))
    stripe_test_user_id = factory.LazyAttribute(lazy_setting('STRIPE_TEST_EVENT_USER_ID'))

    dwolla_test_user_id = factory.LazyAttribute(lazy_setting('DWOLLA_TEST_EVENT_USER_ID'))
    dwolla_test_access_token = factory.LazyAttribute(lazy_setting('DWOLLA_TEST_EVENT_ACCESS_TOKEN'))


class OrderFactory(factory.DjangoModelFactory):
    class Meta:
        model = Order

    event = factory.SubFactory(EventFactory)
    status = Order.IN_PROGRESS
    dwolla_test_user_id = factory.LazyAttribute(lazy_setting('DWOLLA_TEST_USER_USER_ID'))
    dwolla_test_access_token = factory.LazyAttribute(lazy_setting('DWOLLA_TEST_USER_ACCESS_TOKEN'))
