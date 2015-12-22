from datetime import timedelta

from django.utils.timezone import now
import factory

from brambling.models import (
    Event, Person, Order, CreditCard, Invite,
    Organization, Transaction, Item, ItemOption,
    Discount, Attendee, ItemImage, SavedReport,
    CustomForm, CustomFormField, DwollaAccount,
)
from brambling.utils.payment import DWOLLA_SCOPE


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


class DwollaUserAccountFactory(factory.DjangoModelFactory):
    class Meta:
            model = DwollaAccount

    api_type = DwollaAccount.TEST
    user_id = factory.LazyAttribute(lazy_setting('DWOLLA_TEST_USER_USER_ID'))
    access_token = factory.LazyAttribute(lazy_setting('DWOLLA_TEST_USER_ACCESS_TOKEN'))
    refresh_token = factory.LazyAttribute(lazy_setting('DWOLLA_TEST_USER_REFRESH_TOKEN'))
    access_token_expires = now() + timedelta(days=1)
    refresh_token_expires = now() + timedelta(days=2)
    scopes = DWOLLA_SCOPE


class DwollaOrganizationAccountFactory(factory.DjangoModelFactory):
    class Meta:
            model = DwollaAccount

    api_type = DwollaAccount.TEST
    user_id = factory.LazyAttribute(lazy_setting('DWOLLA_TEST_ORGANIZATION_USER_ID'))
    access_token = factory.LazyAttribute(lazy_setting('DWOLLA_TEST_ORGANIZATION_ACCESS_TOKEN'))
    refresh_token = factory.LazyAttribute(lazy_setting('DWOLLA_TEST_ORGANIZATION_REFRESH_TOKEN'))
    access_token_expires = now() + timedelta(days=1)
    refresh_token_expires = now() + timedelta(days=2)
    scopes = DWOLLA_SCOPE


class PersonFactory(factory.DjangoModelFactory):
    class Meta:
        model = Person

    given_name = factory.Sequence(lambda n: "User{}".format(n))
    surname = "Test"

    email = factory.Sequence(lambda n: "test{}@test.com".format(n))
    confirmed_email = factory.LazyAttribute(lambda obj: obj.email)


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

        if extracted:
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


class ItemImageFactory(factory.DjangoModelFactory):
    class Meta:
        model = ItemImage

    item = factory.SubFactory(ItemFactory)
    order = 1
    image = 'path/to/nothing.png'


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


class SavedReportFactory(factory.DjangoModelFactory):
    class Meta:
        model = SavedReport

    report_type = SavedReport.ATTENDEE
    event = factory.SubFactory(EventFactory)
    name = factory.Sequence(lambda n: "Saved Report {}".format(n))
    querystring = ''


class CustomFormFactory(factory.DjangoModelFactory):
    class Meta:
        model = CustomForm

    form_type = CustomForm.ATTENDEE
    event = factory.SubFactory(EventFactory)
    name = factory.Sequence(lambda n: "Custom Form {}".format(n))
    index = 1


class CustomFormFieldFactory(factory.DjangoModelFactory):
    class Meta:
        model = CustomFormField

    field_type = CustomFormField.TEXT
    form = factory.SubFactory(CustomFormFactory)
    name = factory.Sequence(lambda n: "Custom Form Field {}".format(n))
