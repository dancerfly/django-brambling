from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField


# TODO: "meta" class for groups of events? For example, annual events?
class Event(models.Model):
    WORKSHOP = 'workshop'
    EXCHANGE = 'exchange'
    RECESS = 'recess'
    OTHER = 'other'

    CATEGORIES = (
        (WORKSHOP, _("Workshop weekend")),
        (EXCHANGE, _("Exchange")),
        (RECESS, _("Recess")),
        (OTHER, _("Other")),
    )
    name = models.CharField(max_length=50)
    slug = models.CharField(max_length=50)
    tagline = models.CharField(max_length=75)
    city = models.CharField(max_length=50)
    state_or_province = models.CharField(max_length=50)
    country = CountryField()
    currency = models.CharField(max_length=10, default='USD')
    start_date = models.DateField()
    end_date = models.DateField()
    category = models.CharField(max_length=8, choices=CATEGORIES)
    handle_housing = models.BooleanField(default=True)


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


class ItemOption(models.Model):
    item = models.ForeignKey(Item)
    name = models.CharField(max_length=30, blank=True)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    total_number = models.PositiveSmallIntegerField()
    available_start = models.DateTimeField()
    available_end = models.DateTimeField()


class UserItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    item_option = models.ForeignKey(ItemOption)
    reserved = models.DateTimeField(default=now)
    paid = models.DateTimeField(blank=True, null=True)


class ItemDiscount(models.Model):
    item = models.ForeignKey(Item)
    discount = models.ForeignKey('DiscountCode')
    percent = models.DecimalField(max_digits=5, decimal_places=2,
                                  blank=True, null=True,
                                  validators=[MaxValueValidator(100),
                                              MinValueValidator(0)])
    amount = models.DecimalField(max_digits=5, decimal_places=2,
                                 blank=True, null=True,
                                 validators=[MinValueValidator(0)])


class DiscountCode(models.Model):
    code = models.CharField(max_length=20)
    items = models.ManyToManyField(Item, through=ItemDiscount)
    available_start = models.DateTimeField()
    available_end = models.DateTimeField()


class UserDiscount(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    discount = models.ForeignKey(DiscountCode)
    timestamp = models.DateTimeField(default=now)


class Payment(models.Model):
    event = models.ForeignKey(Event)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    amount = models.DecimalField(max_digits=5, decimal_places=2)
    timestamp = models.DateTimeField(default=now)


class EventUserInfo(models.Model):
    LATE = 'late'
    EARLY = 'early'
    LEAD = 'lead'
    FOLLOW = 'follow'
    SWITCH = 'switch'
    AMBI = 'ambi'

    BEDTIME_CHOICES = (
        (LATE, _("Staying up late")),
        (EARLY, _("Going to bed early"))
    )
    MORNING_CHOICES = (
        (LATE, _("Get up when you get up")),
        (EARLY, _("There first thing."))
    )
    ROLES = (
        (LEAD, _("Lead")),
        (FOLLOW, _("Follow")),
        (SWITCH, _("Switch")),
        (AMBI, _("Ambi")),
    )
    event = models.ForeignKey(Event)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)

    # Dancer info.
    #: "What is/are your primary role(s) for the weekend?"
    roles = models.CharField(max_length=6, choices=ROLES)

    # Housing info.
    house_spaces = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(100)])
    nights = models.CommaSeparatedIntegerField(max_length=50)
    car_spaces = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(50)])
    bedtime = models.CharField(max_length=5, choices=BEDTIME_CHOICES)
    wakeup = models.CharField(max_length=5, choices=BEDTIME_CHOICES)
    # These fields actually indicate things people "can't be around" /
    # dislike. Better way of putting it?
    # Could be a Set field?
    avoid_problems = models.CommaSeparatedIntegerField(blank=True, max_length=16)
    avoid_problems_other = models.CharField(max_length=50, blank=True)
    cause_problems = models.CommaSeparatedIntegerField(blank=True, max_length=16)
    cause_problems_other = models.CharField(max_length=50, blank=True)

    request_matches = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                             related_name='requested_matches')
    request_unmatches = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                               related_name='requested_unmatches')

    other = models.TextField(blank=True)


class UserPreferences(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL)

    city = models.CharField(max_length=50)
    state_or_province = models.CharField(max_length=50)
    country = CountryField()
    # Number where you can be reached *during events*
    phone = models.CharField(max_length=50)

    # Some defaults for housing.
    avoid_problems = models.CommaSeparatedIntegerField(blank=True, max_length=16)
    avoid_problems_other = models.CharField(max_length=50, blank=True)
    match_request = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                           related_name='match_requested')
    unmatch_request = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                             related_name='unmatch_requested')
