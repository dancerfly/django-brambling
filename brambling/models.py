from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.validators import MaxValueValidator, MinValueValidator
from django.dispatch import receiver
from django.db import models
from django.db.models import signals
from django.utils.encoding import smart_text
from django.utils.timezone import now
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


@receiver(signals.post_migrate)
def create_default_styles_and_types(app_config, **kwargs):
    if not DanceStyle.objects.exists() and not EventType.objects.exists():
        if kwargs.get('verbosity') >= 2:
            print("Creating default dance styles and event types")

        for name, event_types in DEFAULT_DANCE_STYLES.items():
            style = DanceStyle.objects.create(name=name)
            for event_type in event_types:
                style.common_event_types.add(
                    EventType.objects.get_or_create(name=event_type)[0])


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
    start_date = models.DateField()
    end_date = models.DateField()

    dance_style = models.ForeignKey(DanceStyle, blank=True, null=True)
    event_type = models.ForeignKey(EventType, blank=True, null=True)

    privacy = models.CharField(max_length=7, choices=PRIVACY_CHOICES,
                               default=PUBLIC)

    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              related_name='owner_events')
    editors = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                     related_name='editor_events',
                                     blank=True, null=True)

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
    PRIVATE = 'private'
    PASS = 'pass'

    CATEGORIES = (
        (MERCHANDISE, _("Merchandise")),
        (COMPETITION, _("Competition")),
        (PRIVATE, _("Private lesson")),
        (PASS, _("Pass")),
    )

    name = models.CharField(max_length=30)
    description = models.TextField()
    category = models.CharField(max_length=7, choices=CATEGORIES)
    event = models.ForeignKey(Event)

    def __unicode__(self):
        return smart_text(self.name)


class ItemOption(models.Model):
    item = models.ForeignKey(Item)
    name = models.CharField(max_length=30)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    total_number = models.PositiveSmallIntegerField()
    available_start = models.DateTimeField()
    available_end = models.DateTimeField()

    def __unicode__(self):
        return smart_text(self.name)


class UserItem(models.Model):
    item_option = models.ForeignKey(ItemOption)
    reserved = models.DateTimeField(default=now)
    paid_at = models.DateTimeField(blank=True, null=True)
    paid_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                related_name="items_bought")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
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


class UserDiscount(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    discount = models.ForeignKey(Discount)
    timestamp = models.DateTimeField(default=now)


class Payment(models.Model):
    event = models.ForeignKey(Event)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    amount = models.DecimalField(max_digits=5, decimal_places=2)
    timestamp = models.DateTimeField(default=now)


class EnvironmentalFactor(models.Model):
    name = models.CharField(max_length=30)

    def __unicode__(self):
        return smart_text(self.name)


@receiver(signals.post_migrate)
def create_default_factors(app_config, **kwargs):
    if not EnvironmentalFactor.objects.exists():
        if kwargs.get('verbosity') >= 2:
            print("Creating default environmental factors")
        EnvironmentalFactor.objects.bulk_create([
            EnvironmentalFactor(name=name)
            for name in DEFAULT_ENVIRONMENTAL_FACTORS
        ])


class DietaryRestriction(models.Model):
    name = models.CharField(max_length=20)

    def __unicode__(self):
        return smart_text(self.name)


@receiver(signals.post_migrate)
def create_default_restrictions(app_config, **kwargs):
    if not DietaryRestriction.objects.exists():
        if kwargs.get('verbosity') >= 2:
            print("Creating default dietary restrictions")
        DietaryRestriction.objects.bulk_create([
            DietaryRestriction(name=name)
            for name in DEFAULT_DIETARY_RESTRICTIONS
        ])


class UserInfo(models.Model):
    LATE = 'late'
    EARLY = 'early'

    BEDTIME_CHOICES = (
        (LATE, _("Staying up late")),
        (EARLY, _("Going to bed early"))
    )
    MORNING_CHOICES = (
        (LATE, _("Get up when you get up")),
        (EARLY, _("There first thing."))
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL)

    dietary_restrictions = models.ManyToManyField(DietaryRestriction,
                                                  blank=True)
    phone = models.CharField(max_length=50, blank=True)

    ef_cause = models.ManyToManyField(EnvironmentalFactor,
                                      related_name='user_cause',
                                      blank=True)

    ef_avoid_strong = models.ManyToManyField(EnvironmentalFactor,
                                             related_name='user_avoid_strong',
                                             blank=True)

    ef_avoid_weak = models.ManyToManyField(EnvironmentalFactor,
                                           related_name='user_avoid_weak',
                                           blank=True)

    user_prefer_strong = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                                related_name='user_prefer_strong',
                                                blank=True)

    user_prefer_weak = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                              related_name='user_prefer_weak',
                                              blank=True)

    user_avoid_strong = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                               related_name='user_avoid_strong',
                                               blank=True)

    user_avoid_weak = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                             related_name='user_avoid_weak',
                                             blank=True)


class House(models.Model):
    # People who live in slash can edit the house.
    residents = models.ManyToManyField(settings.AUTH_USER_MODEL)

    address = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=50, blank=True)
    state_or_province = models.CharField(max_length=50, blank=True)
    country = CountryField(blank=True)

    spaces_default = models.PositiveSmallIntegerField(default=0,
                                                      validators=[MaxValueValidator(100)])

    ef_present = models.ManyToManyField(EnvironmentalFactor,
                                        related_name='house_present',
                                        blank=True)

    ef_avoid_strong = models.ManyToManyField(EnvironmentalFactor,
                                             related_name='house_avoid_strong',
                                             blank=True)

    ef_avoid_weak = models.ManyToManyField(EnvironmentalFactor,
                                           related_name='house_avoid_weak',
                                           blank=True)

    user_prefer_strong = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                                related_name='house_prefer_strong',
                                                blank=True)

    user_prefer_weak = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                              related_name='house_prefer_weak',
                                              blank=True)

    user_avoid_strong = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                               related_name='house_avoid_strong',
                                               blank=True)

    user_avoid_weak = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                             related_name='house_avoid_weak',
                                             blank=True)


class EventUserInfo(models.Model):
    BEDTIME_CHOICES = UserInfo.BEDTIME_CHOICES
    MORNING_CHOICES = UserInfo.MORNING_CHOICES

    event = models.ForeignKey(Event)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)

    # Housing info.
    nights = models.CommaSeparatedIntegerField(max_length=50)
    car_spaces = models.SmallIntegerField(default=0,
                                          validators=[MaxValueValidator(50),
                                                      MinValueValidator(-1)])

    bedtime = models.CharField(max_length=5, choices=BEDTIME_CHOICES)
    wakeup = models.CharField(max_length=5, choices=MORNING_CHOICES)

    other = models.TextField(blank=True)


class EventHouseInfo(models.Model):
    event = models.ForeignKey(Event)
    house = models.ForeignKey(House)

    spaces = models.PositiveSmallIntegerField(default=0,
                                              validators=[MaxValueValidator(100)])
    nights = models.CommaSeparatedIntegerField(max_length=50)


class HousingSlot(models.Model):
    event = models.ForeignKey(Event)
    house = models.ForeignKey(House)
    user = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                  blank=True)
    nights = models.CommaSeparatedIntegerField(max_length=50)
