# encoding: utf8
from datetime import timedelta

from django.contrib.auth.models import (AbstractBaseUser, PermissionsMixin,
                                        BaseUserManager)
from django.core.urlresolvers import reverse
from django.core.validators import (MaxValueValidator, MinValueValidator,
                                    RegexValidator)
from django.dispatch import receiver
from django.db import models
from django.db.models import signals, Count
from django.template.defaultfilters import date
from django.utils import timezone
from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField


FULL_NAME_RE = r"^\w+( \w+)+"


DEFAULT_DANCE_STYLES = {
    "Alt Blues": ["Recess"],
    "Trad Blues": ["Workshop", "Exchange", "Camp"],
    "Fusion": ["Exchange"],
    "Swing": ["Workshop", "Exchange", "Camp"],
    "Contra": ["Workshop", "Camp"],
    "West Coast Swing": [],
    "Argentine Tango": [],
    "Ballroom": [],
    "Folk": [],
}

DEFAULT_ENVIRONMENTAL_FACTORS = (
    "Dogs",
    "Cats",
    "Birds",
    "Bees",
    "Peanuts",
    "Children",
    "Tobacco smoke",
    "Other smoke",
    "Alcohol",
    "Recreational drugs",
)


DEFAULT_DIETARY_RESTRICTIONS = (
    "Gluten free",
    "Vegetarian",
    "Vegan",
    "Kosher",
    "Halal",
)


DEFAULT_HOUSING_CATEGORIES = (
    "Quiet",
    "Noisy",
    "All-dancer",
    "Party",
    "Substance-free",
    "Early bird",
    "Night owl",
    "Co-op",
    "Apartment",
    "House",
)


class EventType(models.Model):
    name = models.CharField(max_length=30, unique=True)

    def __unicode__(self):
        return smart_text(self.name)


class DanceStyle(models.Model):
    name = models.CharField(max_length=30, unique=True)
    common_event_types = models.ManyToManyField(EventType,
                                                related_name="common_for",
                                                blank=True)

    def __unicode__(self):
        return smart_text(self.name)


class EnvironmentalFactor(models.Model):
    name = models.CharField(max_length=30)

    def __unicode__(self):
        return smart_text(self.name)


class DietaryRestriction(models.Model):
    name = models.CharField(max_length=20)

    def __unicode__(self):
        return smart_text(self.name)


class HousingCategory(models.Model):
    name = models.CharField(max_length=20)

    def __unicode__(self):
        return smart_text(self.name)


@receiver(signals.post_migrate)
def create_defaults(app_config, **kwargs):
    if not DanceStyle.objects.exists() and not EventType.objects.exists():
        if kwargs.get('verbosity') >= 2:
            print("Creating default dance styles and event types")

        for name, event_types in DEFAULT_DANCE_STYLES.items():
            style = DanceStyle.objects.create(name=name)
            for event_type in event_types:
                style.common_event_types.add(
                    EventType.objects.get_or_create(name=event_type)[0])
    if not DietaryRestriction.objects.exists():
        if kwargs.get('verbosity') >= 2:
            print("Creating default dietary restrictions")
        DietaryRestriction.objects.bulk_create([
            DietaryRestriction(name=name)
            for name in DEFAULT_DIETARY_RESTRICTIONS
        ])
    if not EnvironmentalFactor.objects.exists():
        if kwargs.get('verbosity') >= 2:
            print("Creating default environmental factors")
        EnvironmentalFactor.objects.bulk_create([
            EnvironmentalFactor(name=name)
            for name in DEFAULT_ENVIRONMENTAL_FACTORS
        ])
    if not HousingCategory.objects.exists():
        if kwargs.get('verbosity') >= 2:
            print("Creating default housing categories")
        HousingCategory.objects.bulk_create([
            HousingCategory(name=name)
            for name in DEFAULT_HOUSING_CATEGORIES
        ])


class Date(models.Model):
    date = models.DateField()

    class Meta:
        ordering = ('date',)

    def __unicode__(self):
        return date(self.date, 'l, F jS')


# TODO: "meta" class for groups of events? For example, annual events?
class Event(models.Model):
    PUBLIC = 'public'
    LINK = 'link'
    PRIVATE = 'private'

    PRIVACY_CHOICES = (
        (PUBLIC, _("List publicly")),
        (LINK, _("Visible to anyone with the link")),
        (PRIVATE, _("Only visible to owner and editors")),
    )
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50,
                            validators=[RegexValidator("[a-z0-9-]+")],
                            help_text="URL-friendly version of the event name."
                                      " Dashes, 0-9, and lower-case a-z only.")
    tagline = models.CharField(max_length=75, blank=True)
    city = models.CharField(max_length=50)
    state_or_province = models.CharField(max_length=50)
    country = CountryField()
    timezone = models.CharField(max_length=40, default='UTC')
    currency = models.CharField(max_length=10, default='USD')

    dates = models.ManyToManyField(Date, related_name='event_dates')
    housing_dates = models.ManyToManyField(Date, blank=True, null=True,
                                           related_name='event_housing_dates')

    dance_style = models.ForeignKey(DanceStyle, blank=True, null=True)
    event_type = models.ForeignKey(EventType, blank=True, null=True)

    privacy = models.CharField(max_length=7, choices=PRIVACY_CHOICES,
                               default=PUBLIC, help_text="Who can view this event.")

    owner = models.ForeignKey('Person',
                              related_name='owner_events')
    editors = models.ManyToManyField('Person',
                                     related_name='editor_events',
                                     blank=True, null=True)

    last_modified = models.DateTimeField(auto_now=True)

    collect_housing_data = models.BooleanField(default=True)
    # Time in minutes.
    cart_timeout = models.PositiveSmallIntegerField(default=15,
                                                    help_text="Minutes before a user's cart expires.")

    def __unicode__(self):
        return smart_text(self.name)

    def get_absolute_url(self):
        return reverse('brambling_event_root', kwargs={'slug': self.slug})

    def editable_by(self, user):
        return (user.is_authenticated() and user.is_active and
                (user.is_superuser or user.pk == self.owner_id or
                 self.editors.filter(pk=user.pk).exists()))


class Item(models.Model):
    MERCHANDISE = 'merch'
    COMPETITION = 'comp'
    CLASS = 'class'
    PASS = 'pass'

    CATEGORIES = (
        (MERCHANDISE, _("Merchandise")),
        (COMPETITION, _("Competition")),
        (CLASS, _("Class/Lesson a la carte")),
        (PASS, _("Pass")),
    )

    name = models.CharField(max_length=30)
    description = models.TextField()
    category = models.CharField(max_length=7, choices=CATEGORIES)
    event = models.ForeignKey(Event, related_name='items')

    created_timestamp = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return smart_text(self.name)


class ItemOption(models.Model):
    item = models.ForeignKey(Item, related_name='options')
    name = models.CharField(max_length=30)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    total_number = models.PositiveSmallIntegerField(blank=True, null=True)
    max_per_owner = models.PositiveSmallIntegerField(blank=True, null=True)
    available_start = models.DateTimeField(default=timezone.now)
    available_end = models.DateTimeField()
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ('order',)

    def __unicode__(self):
        return smart_text(self.name)

    def has_forms(self):
        return self.item.category == Item.PASS


class Discount(models.Model):
    PERCENT = 'percent'
    FLAT = 'flat'

    TYPE_CHOICES = (
        (PERCENT, _('Percent')),
        (FLAT, _('Flat')),
    )
    name = models.CharField(max_length=40)
    code = models.CharField(max_length=20)
    item_option = models.ForeignKey(ItemOption)
    available_start = models.DateTimeField(blank=True, null=True)
    available_end = models.DateTimeField(blank=True, null=True)
    discount_type = models.CharField(max_length=7,
                                     choices=TYPE_CHOICES,
                                     default=PERCENT)
    amount = models.DecimalField(max_digits=5, decimal_places=2,
                                 validators=[MinValueValidator(0)])
    event = models.ForeignKey(Event)

    class Meta:
        unique_together = ('code', 'event')

    def __unicode__(self):
        return self.name


class PersonManager(BaseUserManager):
    def _create_user(self, email, password, name, is_superuser,
                     **extra_fields):
        """
        Creates and saves a User with the given username, email and password.
        """
        now = timezone.now()
        if not email:
            raise ValueError('Email must be given')
        email = self.normalize_email(email)
        name = name or email
        person = self.model(email=email, name=name,
                            is_superuser=is_superuser, last_login=now,
                            created_timestamp=now, **extra_fields)
        person.set_password(password)
        person.save(using=self._db)
        return person

    def create_user(self, email, password=None, name=None, **extra_fields):
        return self._create_user(email, password, name, False, **extra_fields)

    def create_superuser(self, email, password, name=None, **extra_fields):
        return self._create_user(email, password, name, True, **extra_fields)


class Person(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=254, unique=True)
    confirmed_email = models.EmailField(max_length=254)
    name = models.CharField(max_length=100, verbose_name="Full name",
                            validators=[RegexValidator(FULL_NAME_RE)],
                            help_text=u"First Last. Must contain only letters and spaces, with a minimum of 1 space.")
    nickname = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    home = models.ForeignKey('Home', blank=True, null=True,
                             related_name='residents')

    created_timestamp = models.DateTimeField(default=timezone.now, editable=False)

    ### Start custom user requirements
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    @property
    def is_staff(self):
        return self.is_superuser

    is_active = True

    objects = PersonManager()
    ### End custom user requirements

    dietary_restrictions = models.ManyToManyField(DietaryRestriction,
                                                  blank=True,
                                                  null=True)

    ef_cause = models.ManyToManyField(EnvironmentalFactor,
                                      related_name='person_cause',
                                      blank=True,
                                      null=True,
                                      verbose_name="People around me will be exposed to")

    ef_avoid = models.ManyToManyField(EnvironmentalFactor,
                                      related_name='person_avoid',
                                      blank=True,
                                      null=True,
                                      verbose_name="I can't/don't want to be around")

    person_prefer = models.ManyToManyField('self',
                                           related_name='preferred_by',
                                           blank=True,
                                           null=True,
                                           verbose_name="I need to be placed with",
                                           symmetrical=False)

    person_avoid = models.ManyToManyField('self',
                                          related_name='avoided_by',
                                          blank=True,
                                          null=True,
                                          verbose_name="I do not want to be around",
                                          symmetrical=False)

    housing_prefer = models.ManyToManyField(HousingCategory,
                                            related_name='preferred_by',
                                            blank=True,
                                            null=True,
                                            verbose_name="I prefer to stay somewhere that is (a/an)")

    other_needs = models.TextField(blank=True)

    dance_styles = models.ManyToManyField(DanceStyle, blank=True)
    event_types = models.ManyToManyField(EventType, blank=True)

    # Stripe-related fields
    stripe_customer_id = models.CharField(max_length=36, blank=True)
    default_card = models.OneToOneField('CreditCard', blank=True, null=True,
                                        related_name='default_for',
                                        on_delete=models.SET_NULL)

    class Meta:
        verbose_name = _('person')
        verbose_name_plural = _('people')

    def __unicode__(self):
        return smart_text(self.name or self.email)

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.nickname or self.name


class CreditCard(models.Model):
    BRAND_CHOICES = (
        ('Visa', 'Visa'),
        ('American Express', 'American Express'),
        ('MasterCard', 'MasterCard'),
        ('Discover', 'Discover'),
        ('JCB', 'JCB'),
        ('Diners Club', 'Diners Club'),
        ('Unknown', 'Unknown'),
    )
    stripe_card_id = models.CharField(max_length=40)
    person = models.ForeignKey(Person, related_name='cards')
    added = models.DateTimeField(auto_now_add=True)

    exp_month = models.PositiveSmallIntegerField()
    exp_year = models.PositiveSmallIntegerField()
    fingerprint = models.CharField(max_length=32)
    last4 = models.CharField(max_length=4)
    brand = models.CharField(max_length=16)

    def is_default(self):
        return self.person.default_card_id == self.id

    def __unicode__(self):
        return (u"{} " + u"\u2022" * 4 + u"{}").format(self.brand, self.last4)


@receiver(signals.pre_delete, sender=CreditCard)
def delete_stripe_card(sender, instance, **kwargs):
    import stripe
    from django.conf import settings
    stripe.api_key = settings.STRIPE_SECRET_KEY
    customer = stripe.Customer.retrieve(instance.person.stripe_customer_id)
    customer.cards.retrieve(instance.stripe_card_id).delete()


class EventPersonManager(models.Manager):
    def __init__(self, *args, **kwargs):
        super(EventPersonManager, self).__init__(*args, **kwargs)
        self.cache = {}

    def get_cached(self, event, person):
        cache = self.cache.setdefault(self.db, {})
        if (event, person) not in cache:
            cache[(event, person)] = self.get_or_create(event=event,
                                                        person=person)[0]
        event_person = cache[(event, person)]
        if event_person.cart_is_expired():
            event_person.delete_cart()
        return event_person


class EventPerson(models.Model):
    """
    This model represents metadata connecting an event and a person.
    For example, it links to the items that a person has bought. It
    also contains denormalized metadata - for example, the person's
    current balance.
    """

    FLYER = 'flyer'
    FACEBOOK = 'facebook'
    WEBSITE = 'website'
    INTERNET = 'internet'
    FRIEND = 'friend'
    ATTENDEE = 'attendee'
    DANCER = 'dancer'
    OTHER = 'other'

    HEARD_THROUGH_CHOICES = (
        (FLYER, "Flyer"),
        (FACEBOOK, 'Facebook'),
        (WEBSITE, 'Event website'),
        (INTERNET, 'Other website'),
        (FRIEND, 'Friend'),
        (ATTENDEE, 'Former attendee'),
        (DANCER, 'Other dancer'),
        (OTHER, 'Other'),
    )

    event = models.ForeignKey(Event)
    person = models.ForeignKey(Person)

    cart_start_time = models.DateTimeField(blank=True, null=True)
    cart_owners_set = models.BooleanField(default=False)

    # "Survey" questions for EventPerson
    survey_completed = models.BooleanField(default=False)
    heard_through = models.CharField(max_length=8,
                                     choices=HEARD_THROUGH_CHOICES,
                                     blank=True)
    heard_through_other = models.CharField(max_length=128, blank=True)
    send_flyers = models.BooleanField(default=False)
    send_flyers_address = models.CharField(max_length=200, verbose_name='address', blank=True)
    send_flyers_city = models.CharField(max_length=50, verbose_name='city', blank=True)
    send_flyers_state_or_province = models.CharField(max_length=50, verbose_name='state or province', blank=True)
    send_flyers_country = CountryField(verbose_name='country', blank=True)

    providing_housing = models.BooleanField(default=False)

    objects = EventPersonManager()

    @property
    def cart_errors(self):
        if not hasattr(self, '_cart_errors'):
            errors = []

            # EventPerson *always* needs to touch the survey page before checkout.
            if not self.survey_completed:
                errors.append(('Survey must be completed',
                               reverse('brambling_event_survey',
                                       kwargs={'event_slug': self.event.slug})))

            # Hosting data only needs to be provided if event cares and
            # EventPerson says they're hosting.
            if self.event.collect_housing_data and self.providing_housing:
                if not EventHousing.objects.filter(event=self.event, home__residents=self.person).exists():
                    errors.append(('Hosting information must be completed',
                                   reverse('brambling_event_hosting',
                                           kwargs={'event_slug': self.event.slug})))

            # All non-merch items must be assigned to an attendee.
            non_merch = self.bought_items.exclude(item_option__item__category=Item.MERCHANDISE)
            if non_merch.filter(attendee__isnull=True).exists():
                errors.append(('All items in cart must be assigned to an attendee.',
                               reverse('brambling_event_attendee_items',
                                       kwargs={'event_slug': self.event.slug})))

            # All attendees must have at least one non-merch item.
            # All attendees must have basic data filled out.
            # If the event cares about housing, attendees that need housing
            # also need to fill out housing data.
            attendees = self.attendees.annotate(Count('bought_items'))

            # First pass: no extra queries.
            attendees_missing_items = False
            for attendee in attendees:
                if not attendee.basic_completed:
                    errors.append(('{} missing basic data'.format(attendee.name),
                                   reverse('brambling_event_attendee_edit',
                                           kwargs={'event_slug': self.event.slug, 'pk': attendee.pk})))

                if attendee.bought_items__count == 0:
                    attendees_missing_items = True

                if (self.event.collect_housing_data and
                        attendee.housing_status == Attendee.NEED and
                        not attendee.housing_completed):
                    errors.append(('{} missing housing data'.format(attendee.name),
                                   reverse('brambling_event_attendee_housing',
                                           kwargs={'event_slug': self.event.slug})))

            if not attendees_missing_items:
                # Second pass: extra queries.
                for attendee in attendees:
                    if not attendee.bought_items.exclude(item_option__item__category=Item.MERCHANDISE).exists():
                        attendees_missing_items = True

            if attendees_missing_items:
                errors.append(('All attendees must have at least one non-merch item',
                               reverse('brambling_event_attendee_items',
                                       kwargs={'event_slug': self.event.slug})))
            self._cart_errors = errors
        return self._cart_errors

    def cart_is_valid(self):
        """
        Check if the cart is ready to be paid for.

        """
        return not bool(self.cart_errors)

    def requires_attendees(self):
        return self.bought_items.exclude(item_option__item__category=Item.MERCHANDISE).exists()

    def add_to_cart(self, item_option):
        if self.cart_is_expired():
            self.delete_cart()
        BoughtItem.objects.create(
            item_option=item_option,
            event_person=self,
            status=BoughtItem.RESERVED
        )
        if self.cart_start_time is None:
            self.cart_start_time = timezone.now()
            self.save()

    def remove_from_cart(self, bought_item):
        if bought_item.event_person_id == self.id:
            bought_item.delete()
        if not self.has_cart():
            self.cart_start_time = None
            self.save()

    def cart_expire_time(self):
        if self.cart_start_time is None:
            return None
        return self.cart_start_time + timedelta(minutes=self.event.cart_timeout)

    def cart_is_expired(self):
        return (self.cart_start_time is not None and
                timezone.now() > self.cart_expire_time())

    def has_cart(self):
        if self.cart_is_expired():
            self.delete_cart()
        return (self.cart_start_time is not None and
                self.bought_items.filter(status=BoughtItem.RESERVED).exists())

    def delete_cart(self):
        self.bought_items.filter(status=BoughtItem.RESERVED).delete()
        if self.cart_start_time is not None:
            self.cart_start_time = None
            self.save()

    def get_groupable_cart(self):
        return self.bought_items.filter(
            status=BoughtItem.RESERVED
        ).order_by('item_option__item', 'item_option__order', '-added')


class Payment(models.Model):
    event_person = models.ForeignKey('EventPerson', related_name='payments')
    amount = models.DecimalField(max_digits=5, decimal_places=2)
    timestamp = models.DateTimeField(default=timezone.now)
    stripe_charge_id = models.CharField(max_length=40, blank=True)
    card = models.ForeignKey('CreditCard', blank=True, null=True)


class BoughtItem(models.Model):
    """
    Represents an item bought (or reserved) by a person.
    """
    # These are essentially just sugar. They might be used
    # for display, but they don't really guarantee anything.
    RESERVED = 'reserved'
    UNPAID = 'unpaid'
    PAID = 'paid'
    REFUNDED = 'refunded'
    STATUS_CHOICES = (
        (RESERVED, _('Reserved')),
        (UNPAID, _('Unpaid')),
        (PAID, _('Paid')),
        (REFUNDED, _('Refunded')),
    )
    item_option = models.ForeignKey(ItemOption)
    event_person = models.ForeignKey(EventPerson, related_name='bought_items')
    added = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=8,
                              choices=STATUS_CHOICES,
                              default=UNPAID)
    # BoughtItem has a single attendee, but attendee can have
    # more than one BoughtItem. Basic example: Attendee can
    # have more than one class. Or, hypothetically, merch bought
    # by a single person could be assigned to multiple attendees.
    # However, merch doesn't *need* an attendee.
    attendee = models.ForeignKey('Attendee', blank=True, null=True,
                                 related_name='bought_items', on_delete=models.SET_NULL)

    def __unicode__(self):
        return u"{} – {} ({})".format(self.item_option.name,
                                      self.event_person.person.name,
                                      self.pk)


class UsedDiscount(models.Model):
    discount = models.ForeignKey(Discount)
    event_person = models.ForeignKey(EventPerson)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('event_person', 'discount')


class Attendee(models.Model):
    """
    This model represents information attached to an event pass. It is
    by default copied from the pass buyer (if they don't already have a pass).

    """
    NEED = 'need'
    HAVE = 'have'
    HOME = 'home'

    HOUSING_STATUS_CHOICES = (
        (NEED, 'Needs housing'),
        (HAVE, 'Already arranged'),
        (HOME, 'Staying at own home'),
    )
    # Internal tracking data
    event_person = models.ForeignKey(EventPerson, related_name='attendees')
    person = models.ForeignKey(Person, blank=True, null=True)
    person_confirmed = models.BooleanField(default=False)

    # Basic data - always required for attendees.
    basic_completed = models.BooleanField(default=False)
    name = models.CharField(max_length=100, verbose_name="Full name",
                            validators=[RegexValidator(FULL_NAME_RE)],
                            help_text=u"First Last. Must contain only letters and spaces, with a minimum of 1 space.")
    nickname = models.CharField(max_length=50, blank=True)
    email = models.EmailField(max_length=254)
    phone = models.CharField(max_length=50, blank=True)
    liability_waiver = models.BooleanField(default=False)
    photo_consent = models.BooleanField(default=False, verbose_name='I consent to have my photo taken at this event.')
    housing_status = models.CharField(max_length=4, choices=HOUSING_STATUS_CHOICES,
                                      default=HAVE, verbose_name='housing status')

    # Housing information - all optional.
    housing_completed = models.BooleanField(default=False)
    nights = models.ManyToManyField(Date, blank=True, null=True)
    ef_cause = models.ManyToManyField(EnvironmentalFactor,
                                      related_name='eventperson_cause',
                                      blank=True,
                                      null=True,
                                      verbose_name="People around me will be exposed to")
    ef_cause_confirm = models.BooleanField(default=False, error_messages={'blank': 'Must be marked correct.'})

    ef_avoid = models.ManyToManyField(EnvironmentalFactor,
                                      related_name='eventperson_avoid',
                                      blank=True,
                                      null=True,
                                      verbose_name="I can't/don't want to be around")
    ef_avoid_confirm = models.BooleanField(default=False, error_messages={'blank': 'Must be marked correct.'})

    person_prefer = models.ManyToManyField(Person,
                                           related_name='event_preferred_by',
                                           blank=True,
                                           null=True,
                                           verbose_name="I need to be placed with",
                                           symmetrical=False)

    person_avoid = models.ManyToManyField(Person,
                                          related_name='event_avoided_by',
                                          blank=True,
                                          null=True,
                                          verbose_name="I do not want to be around",
                                          symmetrical=False)

    housing_prefer = models.ManyToManyField(HousingCategory,
                                            related_name='event_preferred_by',
                                            blank=True,
                                            null=True,
                                            verbose_name="I prefer to stay somewhere that is (a/an)")

    other_needs = models.TextField(blank=True)

    def __unicode__(self):
        return self.name


class Home(models.Model):
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=50)
    state_or_province = models.CharField(max_length=50)
    country = CountryField()
    public_transit_access = models.BooleanField(default=False,
                                                verbose_name="My/Our house has easy access to public transit")

    ef_present = models.ManyToManyField(EnvironmentalFactor,
                                        related_name='home_present',
                                        blank=True,
                                        null=True,
                                        verbose_name="People in my/our home will be exposed to")

    ef_avoid = models.ManyToManyField(EnvironmentalFactor,
                                      related_name='home_avoid',
                                      blank=True,
                                      null=True,
                                      verbose_name="I/We don't want in my/our home",
                                      help_text="Include resident preferences")

    person_prefer = models.ManyToManyField(Person,
                                           related_name='preferred_by_homes',
                                           blank=True,
                                           null=True,
                                           verbose_name="I/We would love to host",
                                           help_text="Include resident preferences")

    person_avoid = models.ManyToManyField(Person,
                                          related_name='avoided_by_homes',
                                          blank=True,
                                          null=True,
                                          verbose_name="I/We don't want to host",
                                          help_text="Include resident preferences")

    housing_categories = models.ManyToManyField(HousingCategory,
                                                related_name='homes',
                                                blank=True,
                                                null=True,
                                                verbose_name="My/Our home is (a/an)")


class EventHousing(models.Model):
    event = models.ForeignKey(Event)
    home = models.ForeignKey(Home, blank=True, null=True)
    event_person = models.ForeignKey(EventPerson)

    # Eventually add a contact_person field.
    contact_name = models.CharField(max_length=100,
                                    validators=[RegexValidator(FULL_NAME_RE)],
                                    help_text=u"First Last. Must contain only letters and spaces, with a minimum of 1 space.")
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)

    # Duplicated data from Home, plus confirm fields.
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=50)
    state_or_province = models.CharField(max_length=50)
    country = CountryField()
    public_transit_access = models.BooleanField(default=False,
                                                verbose_name="My/Our house has easy access to public transit")

    ef_present = models.ManyToManyField(EnvironmentalFactor,
                                        related_name='eventhousing_present',
                                        blank=True,
                                        null=True,
                                        verbose_name="People in the home will be exposed to")
    ef_present_confirm = models.BooleanField(default=False, error_messages={'blank': 'Must be marked correct.'})

    ef_avoid = models.ManyToManyField(EnvironmentalFactor,
                                      related_name='eventhousing_avoid',
                                      blank=True,
                                      null=True,
                                      verbose_name="I/We don't want in my/our home",
                                      help_text="Include resident preferences")
    ef_avoid_confirm = models.BooleanField(default=False, error_messages={'blank': 'Must be marked correct.'})

    person_prefer = models.ManyToManyField(Person,
                                           related_name='preferred_by_eventhousing',
                                           blank=True,
                                           null=True,
                                           verbose_name="I/We would love to host",
                                           help_text="Include resident preferences")

    person_avoid = models.ManyToManyField(Person,
                                          related_name='avoided_by_eventhousing',
                                          blank=True,
                                          null=True,
                                          verbose_name="I/We don't want to host",
                                          help_text="Include resident preferences")

    housing_categories = models.ManyToManyField(HousingCategory,
                                                related_name='eventhousing',
                                                blank=True,
                                                null=True,
                                                verbose_name="Our home is (a/an)")
    housing_categories_confirm = models.BooleanField(default=False, error_messages={'blank': 'Must be marked correct.'})


class HousingSlot(models.Model):
    eventhousing = models.ForeignKey(EventHousing)
    night = models.ForeignKey(Date)
    spaces = models.PositiveSmallIntegerField(default=0,
                                              validators=[MaxValueValidator(100)])
    spaces_max = models.PositiveSmallIntegerField(default=0,
                                                  validators=[MaxValueValidator(100)])


class HousingAssignment(models.Model):
    # Home plans are ignored when checking against spaces.
    AUTO = 'auto'
    MANUAL = 'manual'
    ASSIGNMENT_TYPE_CHOICES = (
        (AUTO, _("Automatic")),
        (MANUAL, _("Manual"))
    )

    attendee = models.ForeignKey(Attendee)
    slot = models.ForeignKey(HousingSlot)
    assignment_type = models.CharField(max_length=6, choices=ASSIGNMENT_TYPE_CHOICES)
