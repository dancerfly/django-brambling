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


class Cart(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    person = models.ForeignKey('Person')
    event = models.ForeignKey(Event)
    owners_set = models.BooleanField(default=False)

    def expires(self):
        return self.created + timedelta(minutes=self.event.cart_timeout)

    def is_expired(self):
        return timezone.now() > self.expires()

    def get_groupable_contents(self):
        return self.contents.order_by('item_option__item', 'item_option__order', '-added')


class PersonItem(models.Model):
    # These are essentially just sugar. They might be used
    # for display, but they don't really guarantee anything.
    UNPAID = 'unpaid'
    PARTIAL = 'partial'
    PAID = 'paid'
    REFUNDED = 'refunded'
    STATUS_CHOICES = (
        (UNPAID, _('Unpaid')),
        (PARTIAL, _('Partially paid')),
        (PAID, _('Paid')),
        (REFUNDED, _('Refunded')),
    )
    item_option = models.ForeignKey(ItemOption)
    added = models.DateTimeField(auto_now_add=True)
    cart = models.ForeignKey(Cart, related_name='contents',
                             blank=True, null=True)
    status = models.CharField(max_length=8,
                              choices=STATUS_CHOICES,
                              default=UNPAID)
    buyer = models.ForeignKey('Person',
                              related_name="items_bought")
    owner = models.ForeignKey('Person',
                              related_name="items_owned",
                              blank=True, null=True)

    def __unicode__(self):
        return u"{} – {} ({})".format(self.item_option.name,
                                      self.buyer.name,
                                      self.pk)


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


class PersonDiscount(models.Model):
    person = models.ForeignKey('Person')
    discount = models.ForeignKey(Discount)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('person', 'discount')


class Payment(models.Model):
    event = models.ForeignKey(Event)
    person = models.ForeignKey('Person')
    amount = models.DecimalField(max_digits=5, decimal_places=2)
    timestamp = models.DateTimeField(default=timezone.now)
    stripe_charge_id = models.CharField(max_length=40, blank=True)
    card = models.ForeignKey('CreditCard', blank=True, null=True)


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
    name = models.CharField(max_length=100, verbose_name="Full name")
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

    def get_cart(self, event, create=False):
        if not hasattr(self, '_carts'):
            self._carts = {}

        if event not in self._carts:
            try:
                qs = Cart.objects.annotate(total=Count('contents'))
                cart = qs.get(person=self, event=event)
            except Cart.DoesNotExist:
                cart = None
            else:
                # Cache here since we know what these are.
                cart.person = self
                cart.event = event
                if cart.is_expired():
                    cart.delete()
                    cart = None
            if cart is None and create:
                cart = Cart.objects.create(person=self, event=event)
            self._carts[event] = cart
        return self._carts[event]

    def get_discounts(self, event):
        return PersonDiscount.objects.filter(
            discount__event=event,
            person=self
        ).order_by('-timestamp').select_related('discount')


class EventPerson(models.Model):
    NEED = 'need'
    HAVE = 'have'
    HOST = 'host'

    STATUS_CHOICES = (
        (NEED, 'Need housing'),
        (HAVE, 'Already arranged'),
        (HOST, 'Hosting others'),
    )

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
    event_pass = models.OneToOneField(PersonItem)
    is_completed = models.BooleanField(default=False)

    status = models.CharField(max_length=4, choices=STATUS_CHOICES,
                              default=HAVE, verbose_name='housing status')
    liability_waiver = models.BooleanField(default=False)
    photo_consent = models.BooleanField(default=False, verbose_name='I consent to have my photo taken at this event.')
    heard_through = models.CharField(max_length=8, choices=HEARD_THROUGH_CHOICES,
                                     blank=True)
    heard_through_other = models.CharField(max_length=128, blank=True)
    send_flyers = models.BooleanField(default=False)


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
    home = models.ForeignKey(Home)

    point_person = models.ForeignKey(Person)

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


class HousingRequest(models.Model):
    event = models.ForeignKey(Event)
    person = models.ForeignKey(Person)

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


class HousingAssignment(models.Model):
    # Home plans are ignored when checking against spaces.
    AUTO = 'auto'
    MANUAL = 'manual'
    ASSIGNMENT_TYPE_CHOICES = (
        (AUTO, _("Automatic")),
        (MANUAL, _("Manual"))
    )

    data = models.ForeignKey(HousingRequest)
    slot = models.ForeignKey(HousingSlot)
    assignment_type = models.CharField(max_length=6, choices=ASSIGNMENT_TYPE_CHOICES)
