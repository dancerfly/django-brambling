from django.contrib.auth.models import (AbstractBaseUser, PermissionsMixin,
                                        BaseUserManager)
from django.core.urlresolvers import reverse
from django.core.validators import MaxValueValidator, MinValueValidator
from django.dispatch import receiver
from django.db import models
from django.db.models import signals
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
        return self.date.strftime(u'%A')


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
    slug = models.SlugField(max_length=50)
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
                               default=PUBLIC)

    owner = models.ForeignKey('Person',
                              related_name='owner_events')
    editors = models.ManyToManyField('Person',
                                     related_name='editor_events',
                                     blank=True, null=True)

    last_modified = models.DateTimeField(auto_now=True)

    collect_housing_data = models.BooleanField(default=True)
    # Time in minutes.
    reservation_timeout = models.PositiveSmallIntegerField(default=15,
                                                           help_text="Minutes before items bought are removed from cart.")

    def __unicode__(self):
        return smart_text(self.name)

    def get_absolute_url(self):
        return reverse('brambling_event_detail', kwargs={'slug': self.slug})

    def can_edit(self, user):
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
    total_number = models.PositiveSmallIntegerField()
    available_start = models.DateTimeField()
    available_end = models.DateTimeField()
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ('order',)

    def __unicode__(self):
        return smart_text(self.name)


class PersonItem(models.Model):
    # "Reserved" can be lost after time expires.
    RESERVED = 'reserved'
    UNPAID = 'unpaid'
    PARTIAL = 'partial'
    PAID = 'paid'
    STATUS_CHOICES = (
        (RESERVED, _('Reserved')),
        (UNPAID, _('Unpaid')),
        (PARTIAL, _('Partially paid')),
        (PAID, _('Paid')),
    )
    item_option = models.ForeignKey(ItemOption)
    quantity = models.PositiveSmallIntegerField()
    added = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=8,
                              choices=STATUS_CHOICES,
                              default=UNPAID)
    buyer = models.ForeignKey('Person',
                              related_name="items_bought")
    owner = models.ForeignKey('Person',
                              related_name="items_owned")


class ItemDiscount(models.Model):
    PERCENT = 'percent'
    FLAT = 'flat'

    TYPE_CHOICES = (
        (PERCENT, _('Percent')),
        (FLAT, _('Flat')),
    )
    item = models.ForeignKey(Item)
    discount = models.ForeignKey('Discount')
    discount_type = models.CharField(max_length=7,
                                     choices=TYPE_CHOICES,
                                     default=PERCENT)
    amount = models.DecimalField(max_digits=5, decimal_places=2,
                                 blank=True, null=True,
                                 validators=[MinValueValidator(0)])


class Discount(models.Model):
    name = models.CharField(max_length=40)
    code = models.CharField(max_length=20)
    items = models.ManyToManyField(Item, through=ItemDiscount)
    available_start = models.DateTimeField()
    available_end = models.DateTimeField()
    event = models.ForeignKey(Event)

    class Meta:
        unique_together = ('code', 'event')


class PersonDiscount(models.Model):
    person = models.ForeignKey('Person')
    discount = models.ForeignKey(Discount)
    timestamp = models.DateTimeField(default=timezone.now)


class Payment(models.Model):
    event = models.ForeignKey(Event)
    person = models.ForeignKey('Person')
    amount = models.DecimalField(max_digits=5, decimal_places=2)
    timestamp = models.DateTimeField(default=timezone.now)


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

    dance_styles = models.ManyToManyField(DanceStyle, blank=True)
    event_types = models.ManyToManyField(EventType, blank=True)

    class Meta:
        verbose_name = _('person')
        verbose_name_plural = _('people')

    def __unicode__(self):
        return smart_text(self.name or self.email)

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.nickname or self.name


class Home(models.Model):
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=50)
    state_or_province = models.CharField(max_length=50)
    country = CountryField()

    spaces = models.PositiveSmallIntegerField(default=0,
                                              validators=[MaxValueValidator(100)],
                                              verbose_name="Preferred spaces")
    spaces_max = models.PositiveSmallIntegerField(default=0,
                                                  validators=[MaxValueValidator(100)],
                                                  verbose_name="Max spaces")

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
                                      help_text="In addition to resident preferences")

    person_prefer = models.ManyToManyField(Person,
                                           related_name='preferred_by_homes',
                                           blank=True,
                                           null=True,
                                           verbose_name="I/We would love to host",
                                           help_text="In addition to resident preferences")

    person_avoid = models.ManyToManyField(Person,
                                          related_name='avoided_by_homes',
                                          blank=True,
                                          null=True,
                                          verbose_name="I/We don't want to host",
                                          help_text="In addition to resident preferences")

    housing_categories = models.ManyToManyField(HousingCategory,
                                                related_name='homes',
                                                blank=True,
                                                null=True,
                                                verbose_name="Our home is (a/an)")


class EventPerson(models.Model):
    LATE = 'late'
    EARLY = 'early'

    BEDTIME_CHOICES = (
        (LATE, _("Staying up late")),
        (EARLY, _("Going to bed early"))
    )
    MORNING_CHOICES = (
        (LATE, _("I'll be up when I'm up")),
        (EARLY, _("There first thing."))
    )

    event = models.ForeignKey(Event)
    person = models.ForeignKey(Person)

    # Housing info.
    nights = models.ManyToManyField(Date, blank=True, null=True)
    car_spaces = models.SmallIntegerField(default=0,
                                          validators=[MaxValueValidator(50),
                                                      MinValueValidator(-1)])

    bedtime = models.CharField(max_length=5, choices=BEDTIME_CHOICES)
    wakeup = models.CharField(max_length=5, choices=MORNING_CHOICES)

    ef_cause = models.ManyToManyField(EnvironmentalFactor,
                                      related_name='eventperson_cause',
                                      blank=True,
                                      null=True,
                                      verbose_name="People around me will be exposed to")

    ef_avoid = models.ManyToManyField(EnvironmentalFactor,
                                      related_name='eventperson_avoid',
                                      blank=True,
                                      null=True,
                                      verbose_name="I can't/don't want to be around")

    person_prefer = models.ManyToManyField('self',
                                           related_name='event_preferred_by',
                                           blank=True,
                                           null=True,
                                           verbose_name="I need to be placed with",
                                           symmetrical=False)

    person_avoid = models.ManyToManyField('self',
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

    other = models.TextField(blank=True)


class EventHousing(models.Model):
    event = models.ForeignKey(Event)
    home = models.ForeignKey(Home)

    spaces = models.PositiveSmallIntegerField(default=0,
                                              validators=[MaxValueValidator(100)])
    spaces_max = models.PositiveSmallIntegerField(default=0,
                                                  validators=[MaxValueValidator(100)])
    nights = models.ManyToManyField(Date, blank=True, null=True)

    ef_present = models.ManyToManyField(EnvironmentalFactor,
                                        related_name='eventhousing_present',
                                        blank=True,
                                        null=True,
                                        verbose_name="People in the home will be exposed to")

    ef_avoid = models.ManyToManyField(EnvironmentalFactor,
                                      related_name='eventhousing_avoid',
                                      blank=True,
                                      null=True,
                                      verbose_name="I/We don't want in my/our home",
                                      help_text="In addition to resident preferences")

    person_prefer = models.ManyToManyField(Person,
                                           related_name='preferred_by_eventhousing',
                                           blank=True,
                                           null=True,
                                           verbose_name="I/We would love to host",
                                           help_text="In addition to resident preferences")

    person_avoid = models.ManyToManyField(Person,
                                          related_name='avoided_by_eventhousing',
                                          blank=True,
                                          null=True,
                                          verbose_name="I/We don't want to host",
                                          help_text="In addition to resident preferences")

    housing_categories = models.ManyToManyField(HousingCategory,
                                                related_name='eventhousing',
                                                blank=True,
                                                null=True,
                                                verbose_name="Our home is (a/an)")


class HousingSlot(models.Model):
    event = models.ForeignKey(Event)
    home = models.ForeignKey(Home)
    person = models.ManyToManyField(Person,
                                    blank=True)
    nights = models.ManyToManyField(Date, blank=True, null=True)
