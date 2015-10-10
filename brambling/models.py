# encoding: utf8
from __future__ import unicode_literals

from datetime import timedelta
from decimal import Decimal
import itertools
import json

from django.contrib.auth.models import (AbstractBaseUser, PermissionsMixin,
                                        BaseUserManager)
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.core.validators import (MaxValueValidator, MinValueValidator,
                                    RegexValidator)
from django.dispatch import receiver
from django.db import models
from django.db.models import signals, Sum
from django.template.defaultfilters import date
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.datastructures import SortedDict
from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField
import floppyforms.__future__ as forms
import pytz

from brambling.mail import InviteMailer
from brambling.utils.payment import (dwolla_refund, stripe_refund, LIVE,
                                     stripe_test_settings_valid,
                                     stripe_live_settings_valid,
                                     dwolla_test_settings_valid,
                                     dwolla_live_settings_valid)


DEFAULT_DANCE_STYLES = (
    "Alt Blues",
    "Trad Blues",
    "Fusion",
    "Swing",
    "Balboa",
    "Contra",
    "West Coast Swing",
    "Argentine Tango",
    "Ballroom",
    "Folk",
    "Contact Improv",
)

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


class AbstractNamedModel(models.Model):
    "A base model for any model which needs a human name."

    NAME_ORDER_CHOICES = (
        ('GMS', "Given Middle Surname"),
        ('SGM', "Surname Given Middle"),
        ('GS', "Given Surname"),
        ('SG', "Surname Given"),
    )

    NAME_ORDER_PATTERNS = {
        'GMS': "{given} {middle} {surname}",
        'SGM': "{surname} {given} {middle}",
        'GS': "{given} {surname}",
        'SG': "{surname} {given}",
    }

    given_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True)
    surname = models.CharField(max_length=50)
    name_order = models.CharField(max_length=3, choices=NAME_ORDER_CHOICES, default="GMS")

    def get_full_name(self):
        name_dict = {
            'given': self.given_name,
            'middle': self.middle_name,
            'surname': self.surname,
        }
        name_order = self.name_order
        if not self.middle_name:
            if name_order == 'GMS':
                name_order = 'GS'
            elif name_order == 'SGM':
                name_order = 'SG'
        return self.NAME_ORDER_PATTERNS[name_order].format(**name_dict)
    get_full_name.short_description = 'Name'

    def get_short_name(self):
        return self.given_name

    class Meta:
        abstract = True


class AbstractDwollaModel(models.Model):
    class Meta:
        abstract = True

    # Token obtained via OAuth.
    dwolla_user_id = models.CharField(max_length=20, blank=True, default='')
    dwolla_access_token = models.CharField(max_length=50, blank=True, default='')
    dwolla_access_token_expires = models.DateTimeField(blank=True, null=True)
    dwolla_refresh_token = models.CharField(max_length=50, blank=True, default='')
    dwolla_refresh_token_expires = models.DateTimeField(blank=True, null=True)
    dwolla_test_user_id = models.CharField(max_length=20, blank=True, default='')
    dwolla_test_access_token = models.CharField(max_length=50, blank=True, default='')
    dwolla_test_access_token_expires = models.DateTimeField(blank=True, null=True)
    dwolla_test_refresh_token = models.CharField(max_length=50, blank=True, default='')
    dwolla_test_refresh_token_expires = models.DateTimeField(blank=True, null=True)

    def dwolla_live_connected(self):
        return bool(
            dwolla_live_settings_valid() and
            self.dwolla_user_id and
            self.dwolla_refresh_token_expires and
            self.dwolla_refresh_token_expires > timezone.now()
        )

    def dwolla_test_connected(self):
        return bool(
            dwolla_test_settings_valid() and
            self.dwolla_test_user_id and
            self.dwolla_test_refresh_token_expires and
            self.dwolla_test_refresh_token_expires > timezone.now()
        )

    def dwolla_live_can_connect(self):
        return bool(
            dwolla_live_settings_valid() and
            (
                not self.dwolla_user_id or
                self.dwolla_refresh_token_expires <= timezone.now()
            )
        )

    def dwolla_test_can_connect(self):
        return bool(
            dwolla_live_settings_valid() and
            (
                not self.dwolla_test_user_id or
                self.dwolla_test_refresh_token_expires <= timezone.now()
            )
        )

    def get_dwolla_connect_url(self):
        raise NotImplementedError

    def clear_dwolla_data(self, api_type):
        prefix = "dwolla_" if api_type == LIVE else "dwolla_test_"
        for field in ('user_id', 'access_token', 'refresh_token'):
            setattr(self, prefix + field, '')
        for field in ('refresh_token_expires', 'access_token_expires'):
            setattr(self, prefix + field, None)


class DanceStyle(models.Model):
    name = models.CharField(max_length=30, unique=True)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return smart_text(self.name)


class EnvironmentalFactor(models.Model):
    name = models.CharField(max_length=30, unique=True)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return smart_text(self.name)


class HousingCategory(models.Model):
    name = models.CharField(max_length=20, unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name_plural = 'housing categories'

    def __unicode__(self):
        return smart_text(self.name)


@receiver(signals.post_migrate)
def create_defaults(app_config, **kwargs):
    if app_config.name == 'brambling':
        if not DanceStyle.objects.exists():
            if kwargs.get('verbosity') >= 2:
                print("Creating default dance styles")
            DanceStyle.objects.bulk_create([
                DanceStyle(name=name)
                for name in DEFAULT_DANCE_STYLES
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


class Organization(AbstractDwollaModel):
    DEMO_SLUG = 'demo'

    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50,
                            validators=[RegexValidator("^[a-z0-9-]+$")],
                            help_text="URL-friendly version of the event name."
                                      " Dashes, 0-9, and lower-case a-z only.",
                            unique=True)
    description = models.TextField(blank=True)
    website_url = models.URLField(blank=True, verbose_name="website URL")
    facebook_url = models.URLField(blank=True, verbose_name="facebook URL")
    banner_image = models.ImageField(blank=True)
    city = models.CharField(max_length=50, blank=True)
    state_or_province = models.CharField(max_length=50, verbose_name='state / province', blank=True)
    country = CountryField(default='US', blank=True)
    dance_styles = models.ManyToManyField(DanceStyle, blank=True)

    owner = models.ForeignKey('Person',
                              related_name='owner_orgs')
    editors = models.ManyToManyField('Person',
                                     related_name='editor_orgs',
                                     blank=True, null=True)

    default_event_city = models.CharField(max_length=50, blank=True)
    default_event_state_or_province = models.CharField(max_length=50, verbose_name='state / province', blank=True)
    default_event_country = CountryField(default='US', blank=True)
    default_event_dance_styles = models.ManyToManyField(DanceStyle, blank=True, related_name='organization_event_default_set')
    default_event_timezone = models.CharField(max_length=40, default='America/New_York', blank=True, choices=((tz, tz) for tz in pytz.common_timezones))
    default_event_currency = models.CharField(max_length=10, default='USD', blank=True)
    # This is a secret value set by admins. It will be cached on the event model.
    default_application_fee_percent = models.DecimalField(max_digits=5, decimal_places=2, default=2.5,
                                                          validators=[MaxValueValidator(100), MinValueValidator(0)])

    # These are obtained with Stripe Connect via Oauth.
    stripe_user_id = models.CharField(max_length=32, blank=True, default='')
    stripe_access_token = models.CharField(max_length=32, blank=True, default='')
    stripe_refresh_token = models.CharField(max_length=60, blank=True, default='')
    stripe_publishable_key = models.CharField(max_length=32, blank=True, default='')

    stripe_test_user_id = models.CharField(max_length=32, blank=True, default='')
    stripe_test_access_token = models.CharField(max_length=32, blank=True, default='')
    stripe_test_refresh_token = models.CharField(max_length=60, blank=True, default='')
    stripe_test_publishable_key = models.CharField(max_length=32, blank=True, default='')

    check_payment_allowed = models.BooleanField(default=False)
    check_payable_to = models.CharField(max_length=50, blank=True)

    check_recipient = models.CharField(max_length=50, blank=True)
    check_address = models.CharField(max_length=200, blank=True)
    check_address_2 = models.CharField(max_length=200, blank=True)
    check_city = models.CharField(max_length=50, blank=True)
    check_state_or_province = models.CharField(max_length=50, blank=True, verbose_name='state / province')
    check_zip = models.CharField(max_length=12, blank=True, verbose_name="zip / postal code")
    check_country = CountryField(default='US')

    # Internal tracking fields.
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return smart_text(self.name)

    def get_absolute_url(self):
        return reverse('brambling_organization_detail', kwargs={
            'organization_slug': self.slug,
        })

    def editable_by(self, user):
        return (user.is_authenticated() and user.is_active and
                (user.is_superuser or user.pk == self.owner_id or
                 self.editors.filter(pk=user.pk).exists()))

    def get_dwolla_connect_url(self):
        return reverse('brambling_organization_dwolla_connect',
                       kwargs={'organization_slug': self.slug})

    def stripe_live_connected(self):
        return bool(stripe_live_settings_valid() and self.stripe_user_id)

    def stripe_test_connected(self):
        return bool(stripe_test_settings_valid() and self.stripe_test_user_id)

    def stripe_live_can_connect(self):
        return bool(stripe_live_settings_valid() and not self.stripe_user_id)

    def stripe_test_can_connect(self):
        return bool(stripe_test_settings_valid() and not self.stripe_test_user_id)

    def get_invites(self):
        return Invite.objects.filter(kind=Invite.ORGANIZATION_EDITOR,
                                     content_id=self.pk)

    def is_demo(self):
        return self.slug == Organization.DEMO_SLUG


class Event(models.Model):
    PUBLIC = 'public'
    LINK = 'link'
    HALF_PUBLIC = 'half-public'
    INVITED = 'invited'

    PRIVACY_CHOICES = (
        (PUBLIC, _("Anyone can find and view the event")),
        (LINK, _("Anyone with a direct link can view the event")),
        (HALF_PUBLIC, _("Anyone can find and view the event, but only people who are invited can register")),
        (INVITED, _("Only people invited to the event can see the event and register")),
    )

    LIVE = 'live'
    TEST = 'test'
    API_CHOICES = (
        (LIVE, _('Live')),
        (TEST, _('Test')),
    )

    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50,
                            validators=[RegexValidator("^[a-z0-9-]+$")],
                            help_text="URL-friendly version of the event name."
                                      " Dashes, 0-9, and lower-case a-z only.")
    description = models.TextField(blank=True)
    website_url = models.URLField(blank=True, verbose_name="website URL")
    facebook_url = models.URLField(blank=True, verbose_name="facebook event URL")
    banner_image = models.ImageField(blank=True)
    city = models.CharField(max_length=50)
    state_or_province = models.CharField(max_length=50, verbose_name='state / province')
    country = CountryField(default='US')
    timezone = models.CharField(max_length=40, default='America/New_York', choices=((tz, tz) for tz in pytz.common_timezones))
    currency = models.CharField(max_length=10, default='USD')

    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)

    dance_styles = models.ManyToManyField(DanceStyle, blank=True)
    has_dances = models.BooleanField(verbose_name="Is a dance / Has dance(s)", default=False)
    has_classes = models.BooleanField(verbose_name="Is a class / Has class(es)", default=False)
    liability_waiver = models.TextField(default=_("I hereby release {organization}, its officers, and its employees from all "
                                                  "liability of injury, loss, or damage to personal property associated "
                                                  "with this event. I acknowledge that I understand the content of this "
                                                  "document. I am aware that it is legally binding and I accept it out "
                                                  "of my own free will."), help_text=_("'{event}' and '{organization}' will be automatically replaced with your event and organization names respectively when users are presented with the waiver."))

    transfers_allowed = models.BooleanField(default=True, help_text="Whether users can transfer items directly to other users.")
    privacy = models.CharField(max_length=11, choices=PRIVACY_CHOICES,
                               default=PUBLIC)
    is_published = models.BooleanField(default=False)
    # If an event is "frozen", it can no longer be edited or unpublished.
    is_frozen = models.BooleanField(default=False)
    # Unpublished events can use test APIs, so that event organizers
    # and developers can easily run through things without accidentally
    # charging actual money.
    api_type = models.CharField(max_length=4, choices=API_CHOICES, default=LIVE)

    organization = models.ForeignKey(Organization)
    additional_editors = models.ManyToManyField('Person',
                                                related_name='editor_events',
                                                blank=True, null=True)

    collect_housing_data = models.BooleanField(default=True)
    collect_survey_data = models.BooleanField(default=True)
    check_postmark_cutoff = models.DateField(blank=True, null=True)

    # Time in minutes.
    cart_timeout = models.PositiveSmallIntegerField(default=15,
                                                    help_text="Minutes before a user's cart expires.")

    # This is a secret value set by admins
    application_fee_percent = models.DecimalField(max_digits=5, decimal_places=2, default=2.5,
                                                  validators=[MaxValueValidator(100), MinValueValidator(0)])

    # Internal tracking fields
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('slug', 'organization')

    def __unicode__(self):
        return smart_text(self.name)

    def get_absolute_url(self):
        return reverse('brambling_event_root', kwargs={
            'event_slug': self.slug,
            'organization_slug': self.organization.slug,
        })

    def get_liability_waiver(self):
        return self.liability_waiver.format(event=self.name, organization=self.organization.name)

    def editable_by(self, user):
        return (
            self.organization.editable_by(user) or (
                user.is_authenticated() and
                user.is_active and
                self.additional_editors.filter(pk=user.pk).exists()
            )
        )

    def viewable_by(self, user):
        if self.editable_by(user):
            return True

        if not self.is_published:
            return False

        if self.privacy == self.INVITED:
            if not user.is_authenticated():
                return False
            if not Order.objects.filter(person=user, event=self).exists():
                return False

        return True

    def can_be_published(self):
        return ItemOption.objects.filter(item__event=self).exists()

    def get_invites(self):
        return Invite.objects.filter(kind=Invite.EVENT,
                                     content_id=self.pk)

    def get_editor_invites(self):
        return Invite.objects.filter(kind=Invite.EVENT_EDITOR,
                                     content_id=self.pk)

    def stripe_connected(self):
        if self.api_type == Event.LIVE:
            return self.organization.stripe_live_connected()
        return self.organization.stripe_test_connected()

    def stripe_can_connect(self):
        if self.api_type == Event.LIVE:
            return self.organization.stripe_live_can_connect()
        return self.organization.stripe_test_can_connect()

    def dwolla_connected(self):
        if self.api_type == Event.LIVE:
            return self.organization.dwolla_live_connected()
        return self.organization.dwolla_test_connected()

    def dwolla_can_connect(self):
        if self.api_type == Event.LIVE:
            return self.organization.dwolla_live_can_connect()
        return self.organization.dwolla_test_can_connect()

    def is_demo(self):
        return self.organization.is_demo()

    def get_housing_dates(self):
        return [
            self.start_date + timedelta(n-1)
            for n in xrange((self.end_date - self.start_date).days + 2)
        ]


class Item(models.Model):
    name = models.CharField(max_length=30, help_text="Full pass, dance-only pass, T-shirt, socks, etc.")
    description = models.TextField(blank=True)
    event = models.ForeignKey(Event, related_name='items')

    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return smart_text(self.name)


class ItemImage(models.Model):
    item = models.ForeignKey(Item, related_name='images')
    order = models.PositiveSmallIntegerField()
    image = models.ImageField()


class ItemOption(models.Model):
    TOTAL_AND_REMAINING = 'both'
    TOTAL = 'total'
    REMAINING = 'remaining'
    HIDDEN = 'hidden'
    REMAINING_DISPLAY_CHOICES = (
        (TOTAL_AND_REMAINING, _('Remaining / Total')),
        (TOTAL, _('Total only')),
        (REMAINING, _('Remaining only')),
        (HIDDEN, _("Don't display")),
    )
    item = models.ForeignKey(Item, related_name='options')
    name = models.CharField(max_length=30)
    price = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    total_number = models.PositiveSmallIntegerField(blank=True, null=True, help_text="Leave blank for unlimited.")
    available_start = models.DateTimeField(default=timezone.now)
    available_end = models.DateTimeField()
    remaining_display = models.CharField(max_length=9, default=TOTAL_AND_REMAINING, choices=REMAINING_DISPLAY_CHOICES)
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ('order',)

    def __unicode__(self):
        return smart_text(self.name)

    @property
    def remaining(self):
        if not hasattr(self, 'taken'):
            self.taken = self.boughtitem_set.exclude(status__in=(BoughtItem.REFUNDED, BoughtItem.TRANSFERRED)).count()
        return self.total_number - self.taken


class Discount(models.Model):
    CODE_REGEX = '[0-9A-Za-z \'"~+=]+'
    PERCENT = 'percent'
    FLAT = 'flat'

    TYPE_CHOICES = (
        (FLAT, _('Flat')),
        (PERCENT, _('Percent')),
    )
    name = models.CharField(max_length=40)
    code = models.CharField(max_length=20, validators=[RegexValidator("^{}$".format(CODE_REGEX))],
                            help_text="Allowed characters: 0-9, a-z, A-Z, space, and '\"~+=")
    item_options = models.ManyToManyField(ItemOption)
    available_start = models.DateTimeField(default=timezone.now)
    available_end = models.DateTimeField()
    discount_type = models.CharField(max_length=7,
                                     choices=TYPE_CHOICES,
                                     default=FLAT)
    amount = models.DecimalField(max_digits=5, decimal_places=2,
                                 validators=[MinValueValidator(0)],
                                 verbose_name="discount value")
    event = models.ForeignKey(Event)

    class Meta:
        unique_together = ('code', 'event')

    def __unicode__(self):
        return self.name


class PersonManager(BaseUserManager):
    def _create_user(self, email, password, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given username, email and password.
        """
        now = timezone.now()
        if not email:
            raise ValueError('Email must be given')
        email = self.normalize_email(email)
        person = self.model(email=email, is_superuser=is_superuser,
                            last_login=now, **extra_fields)
        person.set_password(password)
        person.save(using=self._db)
        return person

    def create_user(self, email, password=None, **extra_fields):
        return self._create_user(email, password, False, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        return self._create_user(email, password, True, **extra_fields)


class Person(AbstractDwollaModel, AbstractNamedModel, AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=254, unique=True)
    confirmed_email = models.EmailField(max_length=254)
    home = models.ForeignKey('Home', blank=True, null=True,
                             related_name='residents')

    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    ### Start custom user requirements
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['given_name', 'surname']

    @property
    def is_staff(self):
        return self.is_superuser

    is_active = models.BooleanField(default=True)

    objects = PersonManager()
    ### End custom user requirements

    # Stripe-related fields
    stripe_customer_id = models.CharField(max_length=36, blank=True)
    stripe_test_customer_id = models.CharField(max_length=36, blank=True, default='')

    class Meta:
        verbose_name = _('person')
        verbose_name_plural = _('people')

    def __unicode__(self):
        return self.get_full_name()

    def get_dwolla_connect_url(self):
        return reverse('brambling_user_dwolla_connect')

    def get_organizations(self):
        return Organization.objects.filter(
            models.Q(owner=self) |
            models.Q(editors=self)
        ).order_by('name').distinct()

    def get_claimable_orders(self):
        if self.email != self.confirmed_email:
            return Order.objects.none()
        event_pks = Event.objects.filter(order__person=self).values_list('pk', flat=True).distinct()
        return Order.objects.filter(
            person__isnull=True,
            email=self.email,
        ).exclude(
            event__in=event_pks,
        )

    def get_unclaimable_orders(self):
        if self.email != self.confirmed_email:
            return Order.objects.none()
        event_pks = Event.objects.filter(order__person=self).values_list('pk', flat=True).distinct()
        return Order.objects.filter(
            person__isnull=True,
            email=self.email,
            event__in=event_pks,
        )


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
    LIVE = 'live'
    TEST = 'test'
    API_CHOICES = (
        (LIVE, 'Live'),
        (TEST, 'Test'),
    )
    ICONS = {
        'Visa': 'cc-visa',
        'American Express': 'cc-amex',
        'Discover': 'cc-discover',
        'MasterCard': 'cc-mastercard',
    }
    stripe_card_id = models.CharField(max_length=40)
    api_type = models.CharField(max_length=4, choices=API_CHOICES, default=LIVE)
    person = models.ForeignKey(Person, related_name='cards', blank=True, null=True)
    added = models.DateTimeField(auto_now_add=True)

    exp_month = models.PositiveSmallIntegerField()
    exp_year = models.PositiveSmallIntegerField()
    fingerprint = models.CharField(max_length=32)
    last4 = models.CharField(max_length=4)
    brand = models.CharField(max_length=16)

    is_saved = models.BooleanField(default=False)

    def __unicode__(self):
        return (u"{} " + u"\u2022" * 4 + u"{}").format(self.brand, self.last4)

    def get_icon(self):
        return self.ICONS.get(self.brand, 'credit-card')


class OrderManager(models.Manager):
    _session_key = '_brambling_order_code'

    def _get_session(self, request):
        return request.session.get(self._session_key, {})

    def _set_session_code(self, request, event, code):
        session_orders = self._get_session(request)
        session_orders[str(event.pk)] = code
        request.session[self._session_key] = session_orders

    def _get_session_code(self, request, event):
        session_orders = self._get_session(request)
        if str(event.pk) in session_orders:
            return session_orders[str(event.pk)]
        return None

    def _delete_session_code(self, request, event):
        session_orders = self._get_session(request)
        if str(event.pk) in session_orders:
            del session_orders[str(event.pk)]
            request.session[self._session_key] = session_orders

    def _can_claim(self, order, user):
        # An order can be auto-claimed if:
        # 1. It doesn't have a person.
        # 2. User is authenticated
        # 3. User doesn't have an order for the event yet.
        # 4. Order hasn't checked out yet.
        if order.person_id is not None:
            return False

        if not user.is_authenticated():
            return False

        if Order.objects.filter(person=user, event=order.event_id).exists():
            return False

        if order.bought_items.filter(status__in=(BoughtItem.BOUGHT, BoughtItem.REFUNDED, BoughtItem.TRANSFERRED)).exists():
            return False

        return True

    def for_request(self, event, request, create=True):
        order = None
        created = False

        # Check if the user is authenticated and has an order for this
        # event.
        if request.user.is_authenticated():
            try:
                order = Order.objects.get(
                    event=event,
                    person=request.user,
                )
            except Order.DoesNotExist:
                pass

        # Next, check if there's a session-stored order. Assign it
        # if the order hasn't checked out yet and the user is authenticated.
        if order is None:
            code = self._get_session_code(request, event)
            if code:
                try:
                    order = Order.objects.get(
                        event=event,
                        person__isnull=True,
                        code=code,
                    )
                except Order.DoesNotExist:
                    pass
                else:
                    if self._can_claim(order, request.user):
                        order.person = request.user
                        order.save()
                    elif request.user.is_authenticated():
                        order = None

        if order is None and create:
            # Okay, then create for this user.
            created = True
            person = request.user if request.user and request.user.is_authenticated() else None
            while True:
                code = get_random_string(8, Order.CODE_ALLOWED_CHARS)

                if not Order.objects.filter(event=event, code=code).exists():
                    break

            order = Order.objects.create(event=event, code=code, person=person)

            if not request.user.is_authenticated():
                self._set_session_code(request, event, order.code)

        if order is None:
            raise Order.DoesNotExist

        if order.cart_is_expired():
            order.delete_cart()

        return order, created


class Order(AbstractDwollaModel):
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

    CODE_ALLOWED_CHARS = 'abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'

    event = models.ForeignKey(Event)
    person = models.ForeignKey(Person, blank=True, null=True)
    email = models.EmailField(blank=True)
    code = models.CharField(max_length=8, db_index=True)

    cart_start_time = models.DateTimeField(blank=True, null=True)

    # "Survey" questions for Order
    survey_completed = models.BooleanField(default=False)
    heard_through = models.CharField(max_length=8,
                                     choices=HEARD_THROUGH_CHOICES,
                                     blank=True)
    heard_through_other = models.CharField(max_length=128, blank=True)
    send_flyers = models.BooleanField(default=False)
    send_flyers_address = models.CharField(max_length=200, verbose_name='address', blank=True)
    send_flyers_address_2 = models.CharField(max_length=200, verbose_name='address line 2', blank=True)
    send_flyers_city = models.CharField(max_length=50, verbose_name='city', blank=True)
    send_flyers_state_or_province = models.CharField(max_length=50, verbose_name='state / province', blank=True)
    send_flyers_zip = models.CharField(max_length=12, verbose_name="zip / postal code", blank=True)
    send_flyers_country = CountryField(verbose_name='country', blank=True)

    providing_housing = models.BooleanField(default=False)

    custom_data = GenericRelation('CustomFormEntry', content_type_field='related_ct', object_id_field='related_id')

    # Admin-only data
    notes = models.TextField(blank=True)

    objects = OrderManager()

    class Meta:
        unique_together = ('event', 'code')

    def get_dwolla_connect_url(self):
        return reverse('brambling_order_dwolla_connect',
                       kwargs={'event_slug': self.event.slug,
                               'organization_slug': self.event.organization.slug})

    def dwolla_connected(self):
        if self.api_type == Event.LIVE:
            return self.dwolla_live_connected()
        return self.dwolla_test_connected()

    def dwolla_can_connect(self):
        if self.api_type == Event.LIVE:
            return self.dwolla_live_can_connect()
        return self.dwolla_test_can_connect()

    def add_discount(self, discount, force=False):
        if discount.event_id != self.event_id:
            raise ValueError("Discount is not for the correct event")
        event_person_discount, created = OrderDiscount.objects.get_or_create(
            discount=discount,
            order=self
        )
        if created or force:
            bought_items = BoughtItem.objects.filter(
                order=self,
                item_option__discount=discount,
            ).filter(status__in=(
                BoughtItem.UNPAID,
                BoughtItem.RESERVED,
            )).distinct()
            BoughtItemDiscount.objects.bulk_create([
                BoughtItemDiscount(discount=discount,
                                   bought_item=bought_item,
                                   name=discount.name,
                                   code=discount.code,
                                   discount_type=discount.discount_type,
                                   amount=discount.amount)
                for bought_item in bought_items
            ])
        return created

    def add_to_cart(self, item_option):
        if self.cart_is_expired():
            self.delete_cart()
        bought_item = BoughtItem.objects.create(
            item_option=item_option,
            order=self,
            status=BoughtItem.RESERVED,
            item_name=item_option.item.name,
            item_description=item_option.item.description,
            item_option_name=item_option.name,
            price=item_option.price,
        )
        discounts = self.discounts.filter(
            discount__item_options=item_option
        ).select_related('discount').distinct()
        if discounts:
            BoughtItemDiscount.objects.bulk_create([
                BoughtItemDiscount(discount=discount.discount,
                                   bought_item=bought_item,
                                   name=discount.discount.name,
                                   code=discount.discount.code,
                                   discount_type=discount.discount.discount_type,
                                   amount=discount.discount.amount)
                for discount in discounts
            ])
        if self.cart_start_time is None:
            self.cart_start_time = timezone.now()
            self.save()

    def remove_from_cart(self, bought_item):
        if bought_item.order.id == self.id:
            bought_item.delete()
        if not self.has_cart():
            self.cart_start_time = None
            self.save()

    def mark_cart_paid(self, payment):
        bought_items = self.bought_items.filter(
            status__in=(BoughtItem.RESERVED, BoughtItem.UNPAID)
        )
        payment.bought_items = bought_items
        bought_items.update(status=BoughtItem.BOUGHT)
        if self.cart_start_time is not None:
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
        ).order_by('item_name', 'item_option_name', '-added')

    def get_summary_data(self):
        if self.cart_is_expired():
            self.delete_cart()

        # First, fetch all transactions
        transactions_qs = self.transactions.order_by('-timestamp')
        # First fetch BoughtItems and group by transaction.
        bought_items_qs = self.bought_items.prefetch_related(
            'discounts',
            'transactions',
        ).order_by('-added')

        transactions = SortedDict()

        # Prepopulate transactions dictionary.
        for txn in itertools.chain([None], transactions_qs):
            transactions[txn] = {
                'items': [],
                'discounts': [],
                'gross_cost': 0,
                'total_savings': 0,
                'net_cost': 0,
            }

        def add_item(txn, item):
            txn_dict = transactions[txn]
            txn_dict['items'].append(item)
            multiplier = -1 if txn and txn.transaction_type == Transaction.REFUND else 1
            txn_dict['gross_cost'] += multiplier * item.price
            for discount in item.discounts.all():
                txn_dict['discounts'].append(discount)
                txn_dict["total_savings"] -= multiplier * discount.savings()
            txn_dict['net_cost'] = txn_dict['gross_cost'] + txn_dict['total_savings']

        for item in bought_items_qs:
            if not item.transactions.all():
                add_item(None, item)
            else:
                for txn in item.transactions.all():
                    add_item(txn, item)

        if not transactions[None]['items']:
            del transactions[None]

        gross_cost = 0
        total_savings = 0
        net_cost = 0
        total_payments = 0
        total_refunds = 0
        unconfirmed_check_payments = False

        for txn, txn_dict in transactions.iteritems():
            gross_cost += txn_dict['gross_cost']
            total_savings += txn_dict['total_savings']
            net_cost += txn_dict['net_cost']
            if txn:
                if txn.transaction_type == Transaction.REFUND:
                    total_refunds += txn.amount
                else:
                    total_payments += txn.amount
                    if not unconfirmed_check_payments and txn and txn.method == Transaction.CHECK and not txn.is_confirmed:
                        unconfirmed_check_payments = True

        return {
            'transactions': transactions,
            'gross_cost': gross_cost,
            'total_savings': total_savings,
            'total_refunds': total_refunds,
            'total_payments': total_payments,
            'net_cost': net_cost,
            'net_balance': net_cost - (total_payments + total_refunds),
            'unconfirmed_check_payments': unconfirmed_check_payments
        }

    def get_eventhousing(self):
        # Workaround for DNE exceptions on nonexistant reverse relations.
        if not hasattr(self, '_eventhousing'):
            try:
                self._eventhousing = self.eventhousing
            except EventHousing.DoesNotExist:
                self._eventhousing = None
        return self._eventhousing

    def has_dwolla_payments(self):
        return self.transactions.filter(method=Transaction.DWOLLA).exists()


class Transaction(models.Model):
    STRIPE = 'stripe'
    DWOLLA = 'dwolla'
    CASH = 'cash'
    CHECK = 'check'
    FAKE = 'fake'
    NONE = 'none'

    METHOD_CHOICES = (
        (STRIPE, 'Stripe'),
        (DWOLLA, 'Dwolla'),
        (CASH, 'Cash'),
        (CHECK, 'Check'),
        (FAKE, 'Fake'),
        (NONE, 'No balance change'),
    )

    LIVE = 'live'
    TEST = 'test'
    API_CHOICES = (
        (LIVE, _('Live')),
        (TEST, _('Test')),
    )

    PURCHASE = 'purchase'
    REFUND = 'refund'
    TRANSFER = 'transfer'
    OTHER = 'other'
    TRANSACTION_TYPE_CHOICES = (
        (PURCHASE, _('Purchase')),
        (REFUND, _('Refunded purchase')),
        (TRANSFER, _('Transfer')),
        (OTHER, _('Other')),
    )

    REMOTE_URLS = {
        (STRIPE, PURCHASE, LIVE): 'https://dashboard.stripe.com/payments/{remote_id}',
        (STRIPE, PURCHASE, TEST): 'https://dashboard.stripe.com/test/payments/{remote_id}',
        (STRIPE, REFUND, LIVE): 'https://dashboard.stripe.com/payments/{related_remote_id}',
        (STRIPE, REFUND, TEST): 'https://dashboard.stripe.com/test/payments/{related_remote_id}',
        (DWOLLA, PURCHASE, LIVE): 'https://dwolla.com/activity#/detail/{remote_id}',
        (DWOLLA, PURCHASE, TEST): 'https://uat.dwolla.com/activity#/detail/{remote_id}',
        (DWOLLA, REFUND, LIVE): 'https://dwolla.com/activity#/detail/{remote_id}',
        (DWOLLA, REFUND, TEST): 'https://uat.dwolla.com/activity#/detail/{remote_id}',
    }
    amount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    application_fee = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    processing_fee = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    timestamp = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(Person, blank=True, null=True)
    method = models.CharField(max_length=7, choices=METHOD_CHOICES)
    transaction_type = models.CharField(max_length=8, choices=TRANSACTION_TYPE_CHOICES)
    is_confirmed = models.BooleanField(default=False)
    api_type = models.CharField(max_length=4, choices=API_CHOICES, default=LIVE)
    event = models.ForeignKey(Event)

    related_transaction = models.ForeignKey('self', blank=True, null=True, related_name='related_transaction_set')
    order = models.ForeignKey('Order', related_name='transactions', blank=True, null=True)
    remote_id = models.CharField(max_length=40, blank=True)
    card = models.ForeignKey('CreditCard', blank=True, null=True, on_delete=models.SET_NULL)
    bought_items = models.ManyToManyField('BoughtItem', related_name='transactions', blank=True, null=True)

    class Meta:
        get_latest_by = 'timestamp'

    def get_remote_url(self):
        key = (self.method, self.transaction_type, self.api_type)
        if self.remote_id and key in Transaction.REMOTE_URLS:
            return Transaction.REMOTE_URLS[key].format(
                remote_id=self.remote_id,
                related_remote_id=self.related_transaction.remote_id if self.related_transaction else ''
            )
        return None

    @classmethod
    def from_stripe_charge(cls, charge, **kwargs):
        # charge is expected to be a stripe charge with
        # balance_transaction expanded.
        application_fee = 0
        processing_fee = 0
        for fee in charge.balance_transaction.fee_details:
            if fee.type == 'application_fee':
                application_fee = Decimal(fee.amount) / 100
            elif fee.type == 'stripe_fee':
                processing_fee = Decimal(fee.amount) / 100
        return Transaction.objects.create(
            transaction_type=Transaction.PURCHASE,
            amount=Decimal(charge.amount) / 100,
            method=Transaction.STRIPE,
            remote_id=charge.id,
            is_confirmed=True,
            application_fee=application_fee,
            processing_fee=processing_fee,
            **kwargs
        )

    @classmethod
    def from_stripe_refund(cls, refund, related_transaction, **kwargs):
        application_fee_refund = refund['application_fee_refund']
        refund = refund['refund']
        processing_fee = 0
        for fee in refund.balance_transaction.fee_details:
            if fee.type == 'stripe_fee':
                processing_fee = Decimal(fee.amount) / 100
        return Transaction.objects.create(
            transaction_type=Transaction.REFUND,
            method=Transaction.STRIPE,
            amount=-1 * Decimal(refund.amount) / 100,
            is_confirmed=True,
            related_transaction=related_transaction,
            remote_id=refund.id,
            application_fee=-1 * Decimal(application_fee_refund.amount) / 100,
            processing_fee=processing_fee,
            **kwargs
        )

    @classmethod
    def from_dwolla_charge(cls, charge, **kwargs):
        application_fee = 0
        processing_fee = 0
        if charge['Fees']:
            for fee in charge['Fees']:
                if fee['Type'] == 'Facilitator Fee':
                    application_fee = Decimal(str(fee['Amount']))
                elif fee['Type'] == 'Dwolla Fee':
                    processing_fee = Decimal(str(fee['Amount']))
        return Transaction.objects.create(
            transaction_type=Transaction.PURCHASE,
            amount=charge['Amount'],
            method=Transaction.DWOLLA,
            remote_id=charge['Id'],
            application_fee=application_fee,
            processing_fee=processing_fee,
            is_confirmed=True if charge['Status'] == 'processed' else False,
            **kwargs
        )

    @classmethod
    def from_dwolla_refund(cls, refund, related_transaction, **kwargs):
        # Dwolla refunds don't AFAICT refund fees.
        return Transaction.objects.create(
            transaction_type=Transaction.REFUND,
            method=Transaction.DWOLLA,
            amount=-1 * refund['Amount'],
            is_confirmed=True,
            related_transaction=related_transaction,
            remote_id=refund['TransactionId'],
            **kwargs
        )

    def can_refund(self):
        refunded = self.related_transaction_set.filter(
            transaction_type=Transaction.REFUND
        ).aggregate(refunded=Sum('amount'))['refunded'] or 0
        return self.amount + refunded > 0

    def refund(self, amount=None, bought_items=None, issuer=None, dwolla_pin=None):
        if amount is None:
            amount = self.amount
        if bought_items is None:
            bought_items = self.bought_items.all()

        total_refunds = self.related_transaction_set.aggregate(Sum('amount'))['amount__sum'] or 0
        refundable = self.amount + total_refunds
        if refundable < amount:
            raise ValueError("Not enough money available")

        if refundable == 0:
            return None

        refund_kwargs = {
            'order': self.order,
            'related_transaction': self,
            'api_type': self.api_type,
            'created_by': issuer,
            'event': self.event,
        }

        # May raise an error
        if self.method == Transaction.STRIPE:
            refund = stripe_refund(
                event=self.order.event,
                order=self.order,
                payment_id=self.remote_id,
                amount=refundable,
            )
            txn = Transaction.from_stripe_refund(refund, **refund_kwargs)
        elif self.method == Transaction.DWOLLA:
            refund = dwolla_refund(
                order=self.order,
                event=self.order.event,
                payment_id=self.remote_id,
                amount=refundable,
                pin=dwolla_pin,
            )
            txn = Transaction.from_dwolla_refund(refund, **refund_kwargs)
        else:
            txn = Transaction.objects.create(
                transaction_type=Transaction.REFUND,
                amount=-1 * refundable,
                is_confirmed=True,
                remote_id='',
                method=self.method,
                **refund_kwargs
            )
        txn.bought_items = bought_items
        bought_items.update(status=BoughtItem.REFUNDED)
        return txn
    refund.alters_data = True


class BoughtItem(models.Model):
    """
    Represents an item bought (or reserved) by a person.
    """
    # These are essentially just sugar. They might be used
    # for display, but they don't really guarantee anything.
    RESERVED = 'reserved'
    UNPAID = 'unpaid'
    BOUGHT = 'bought'
    REFUNDED = 'refunded'
    TRANSFERRED = 'transferred'
    STATUS_CHOICES = (
        (RESERVED, _('Reserved')),
        (UNPAID, _('Unpaid')),
        (BOUGHT, _('Bought')),
        (REFUNDED, _('Refunded')),
        (TRANSFERRED, _('Transferred')),
    )
    item_option = models.ForeignKey(ItemOption, blank=True, null=True, on_delete=models.SET_NULL)
    order = models.ForeignKey(Order, related_name='bought_items')
    added = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=11,
                              choices=STATUS_CHOICES,
                              default=UNPAID)

    # Values cached at creation time, in case the values change / the
    # referenced items are deleted.
    item_name = models.CharField(max_length=30)
    item_description = models.TextField(blank=True)
    item_option_name = models.CharField(max_length=30)
    price = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])

    # BoughtItem has a single attendee, but attendee can have
    # more than one BoughtItem. Basic example: Attendee can
    # have more than one class. Or, hypothetically, merch bought
    # by a single person could be assigned to multiple attendees.
    attendee = models.ForeignKey('Attendee', blank=True, null=True,
                                 related_name='bought_items', on_delete=models.SET_NULL)

    class Meta:
        ordering = ('added',)

    def __unicode__(self):
        return u"{} – {} ({})".format(self.item_option_name,
                                      self.order.code,
                                      self.pk)


class OrderDiscount(models.Model):
    """Tracks whether a person has entered a code for an event."""
    discount = models.ForeignKey(Discount)
    order = models.ForeignKey(Order, related_name='discounts')
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('order', 'discount')


class BoughtItemDiscount(models.Model):
    """"Tracks whether an item has had a discount applied to it."""
    PERCENT = 'percent'
    FLAT = 'flat'

    TYPE_CHOICES = (
        (FLAT, _('Flat')),
        (PERCENT, _('Percent')),
    )
    discount = models.ForeignKey(Discount, blank=True, null=True, on_delete=models.SET_NULL)
    bought_item = models.ForeignKey(BoughtItem, related_name='discounts')
    timestamp = models.DateTimeField(default=timezone.now)

    # Values cached at creation time, in case the values change / the
    # referenced items are deleted.
    name = models.CharField(max_length=40)
    code = models.CharField(max_length=20)
    discount_type = models.CharField(max_length=7,
                                     choices=TYPE_CHOICES,
                                     default=FLAT)
    amount = models.DecimalField(max_digits=5, decimal_places=2,
                                 validators=[MinValueValidator(0)])

    class Meta:
        unique_together = ('bought_item', 'code')

    def savings(self):
        return min(self.amount
                   if self.discount_type == BoughtItemDiscount.FLAT
                   else self.amount / 100 * self.bought_item.price,
                   self.bought_item.price)


class HousingRequestNight(models.Model):
    date = models.DateField()

    class Meta:
        ordering = ('date',)

    def __unicode__(self):
        return date(self.date, 'l, F jS')


@receiver(signals.post_save, sender=Event)
def create_request_nights(sender, instance, **kwargs):
    """
    At some point in the future, we might want to switch this to
    a ForeignKey relationship in the other direction, and let folks
    annotate each night with specific information. For now, for simplicity,
    we're sticking with the relationship that already exists.
    """
    date_set = set(instance.get_housing_dates())
    seen = set(HousingRequestNight.objects.filter(date__in=date_set).values_list('date', flat=True))
    to_create = date_set - seen
    if to_create:
        HousingRequestNight.objects.bulk_create([
            HousingRequestNight(date=date) for date in to_create
        ])


class Attendee(AbstractNamedModel):
    """
    This model represents information about someone attending an event.

    """
    NEED = 'need'
    HAVE = 'have'
    HOME = 'home'

    HOUSING_STATUS_CHOICES = (
        (NEED, 'Needs housing'),
        (HAVE, 'Already arranged / hosting not required'),
        (HOME, 'Staying at own home'),
    )
    # Internal tracking data
    order = models.ForeignKey(Order, related_name='attendees')
    saved_attendee = models.ForeignKey('SavedAttendee', blank=True, null=True, on_delete=models.SET_NULL)

    # Basic data - always required for attendees.
    basic_completed = models.BooleanField(default=False)
    email = models.EmailField(max_length=254)
    phone = models.CharField(max_length=50, blank=True)
    liability_waiver = models.BooleanField(default=False, help_text="Must be agreed to by the attendee themselves.")
    photo_consent = models.BooleanField(default=False, verbose_name='I consent to have my photo taken at this event.')
    housing_status = models.CharField(max_length=4, choices=HOUSING_STATUS_CHOICES,
                                      default=HAVE, verbose_name='housing status')

    # Housing information - all optional.
    housing_completed = models.BooleanField(default=False)
    nights = models.ManyToManyField(HousingRequestNight, blank=True, null=True)
    ef_cause = models.ManyToManyField(EnvironmentalFactor,
                                      related_name='attendee_cause',
                                      blank=True,
                                      null=True,
                                      verbose_name="People around me may be exposed to")

    ef_avoid = models.ManyToManyField(EnvironmentalFactor,
                                      related_name='attendee_avoid',
                                      blank=True,
                                      null=True,
                                      verbose_name="I can't/don't want to be around")

    person_prefer = models.TextField(blank=True,
                                     verbose_name="I need to be placed with these people",
                                     help_text="Provide a list of names, separated by line breaks.")

    person_avoid = models.TextField(blank=True,
                                    verbose_name="I do not want to be around these people",
                                    help_text="Provide a list of names, separated by line breaks.")

    housing_prefer = models.ManyToManyField(HousingCategory,
                                            related_name='event_preferred_by',
                                            blank=True,
                                            null=True,
                                            verbose_name="I prefer to stay somewhere that is (a/an)")

    other_needs = models.TextField(blank=True)

    custom_data = GenericRelation('CustomFormEntry', content_type_field='related_ct', object_id_field='related_id')

    def __unicode__(self):
        return self.get_full_name()

    def get_groupable_items(self):
        return self.bought_items.order_by('item_name', 'item_option_name', '-added')


class SavedAttendee(AbstractNamedModel):
    person = models.ForeignKey(Person)
    email = models.EmailField(max_length=254)
    phone = models.CharField(max_length=50, blank=True)
    ef_cause = models.ManyToManyField(EnvironmentalFactor,
                                      related_name='saved_attendee_cause',
                                      blank=True,
                                      null=True,
                                      verbose_name="People around me may be exposed to")

    ef_avoid = models.ManyToManyField(EnvironmentalFactor,
                                      related_name='saved_attendee_avoid',
                                      blank=True,
                                      null=True,
                                      verbose_name="I can't/don't want to be around")

    person_prefer = models.TextField(blank=True,
                                     verbose_name="I need to be placed with these people",
                                     help_text="Provide a list of names, separated by line breaks.")

    person_avoid = models.TextField(blank=True,
                                    verbose_name="I do not want to be around these people",
                                    help_text="Provide a list of names, separated by line breaks.")

    housing_prefer = models.ManyToManyField(HousingCategory,
                                            blank=True,
                                            null=True,
                                            verbose_name="I prefer to stay somewhere that is (a/an)")

    other_needs = models.TextField(blank=True)

    # Internal tracking fields.
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.get_full_name()


class Home(models.Model):
    address = models.CharField(max_length=200)
    address_2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=50)
    state_or_province = models.CharField(max_length=50, verbose_name='state / province')
    zip_code = models.CharField(max_length=12, blank=True, verbose_name="zip / postal code")
    country = CountryField()
    public_transit_access = models.BooleanField(default=False,
                                                verbose_name="My/Our house has easy access to public transit")

    ef_present = models.ManyToManyField(EnvironmentalFactor,
                                        related_name='home_present',
                                        blank=True,
                                        null=True,
                                        verbose_name="People in my/our home may be exposed to")

    ef_avoid = models.ManyToManyField(EnvironmentalFactor,
                                      related_name='home_avoid',
                                      blank=True,
                                      null=True,
                                      verbose_name="I/We don't want in my/our home")

    person_prefer = models.TextField(blank=True,
                                     verbose_name="I/We would love to host",
                                     help_text="Provide a list of names, separated by line breaks.")

    person_avoid = models.TextField(blank=True,
                                    verbose_name="I/We don't want to host",
                                    help_text="Provide a list of names, separated by line breaks.")

    housing_categories = models.ManyToManyField(HousingCategory,
                                                related_name='homes',
                                                blank=True,
                                                null=True,
                                                verbose_name="My/Our home is (a/an)")


class EventHousing(models.Model):
    event = models.ForeignKey(Event)
    home = models.ForeignKey(Home, blank=True, null=True, on_delete=models.SET_NULL)
    order = models.OneToOneField(Order, related_name='eventhousing')

    # Eventually add a contact_person field.
    contact_name = models.CharField(max_length=100)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50)

    # Duplicated data from Home, plus confirm fields.
    address = models.CharField(max_length=200)
    address_2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=50)
    state_or_province = models.CharField(max_length=50, verbose_name='state / province')
    zip_code = models.CharField(max_length=12, blank=True, verbose_name="zip / postal code")
    country = CountryField()
    public_transit_access = models.BooleanField(default=False,
                                                verbose_name="My/Our house has easy access to public transit")

    ef_present = models.ManyToManyField(EnvironmentalFactor,
                                        related_name='eventhousing_present',
                                        blank=True,
                                        null=True,
                                        verbose_name="People in the home may be exposed to")

    ef_avoid = models.ManyToManyField(EnvironmentalFactor,
                                      related_name='eventhousing_avoid',
                                      blank=True,
                                      null=True,
                                      verbose_name="I/We don't want in my/our home")

    person_prefer = models.TextField(blank=True,
                                     verbose_name="I/We would love to host",
                                     help_text="Provide a list of names, separated by line breaks.")

    person_avoid = models.TextField(blank=True,
                                    verbose_name="I/We don't want to host",
                                    help_text="Provide a list of names, separated by line breaks.")

    housing_categories = models.ManyToManyField(HousingCategory,
                                                related_name='eventhousing',
                                                blank=True,
                                                null=True,
                                                verbose_name="Our home is (a/an)")

    custom_data = GenericRelation('CustomFormEntry', content_type_field='related_ct', object_id_field='related_id')


class HousingSlot(models.Model):
    eventhousing = models.ForeignKey(EventHousing)
    date = models.DateField()
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


class InviteManager(models.Manager):
    def get_or_create_invite(self, email, user, kind, content_id):
        while True:
            code = get_random_string(
                length=20,
                allowed_chars='abcdefghijkmnpqrstuvwxyz'
                              'ABCDEFGHJKLMNPQRSTUVWXYZ23456789-~'
            )
            if not Invite.objects.filter(code=code).exists():
                break
        defaults = {
            'user': user,
            'code': code,
        }
        return self.get_or_create(email=email, content_id=content_id, kind=kind, defaults=defaults)


class Invite(models.Model):
    EVENT = 'event'
    EVENT_EDITOR = 'editor'
    ORGANIZATION_EDITOR = 'org_editor'
    TRANSFER = 'transfer'
    KIND_CHOICES = (
        (EVENT, _('Event')),
        (EVENT_EDITOR, _("Event Editor")),
        (ORGANIZATION_EDITOR, _("Organization Editor")),
        (TRANSFER, _("Transfer")),
    )

    objects = InviteManager()
    code = models.CharField(max_length=20, unique=True)
    email = models.EmailField()
    #: User who sent the invitation.
    user = models.ForeignKey(Person, blank=True, null=True)
    is_sent = models.BooleanField(default=False)
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    content_id = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('email', 'content_id', 'kind'),)

    def send(self, site, content=None, secure=False):
        InviteMailer(
            site=site,
            secure=secure,
            invite=self,
            content=content,
            key="invite_{}".format(self.kind),
        ).send()
        self.is_sent = True
        self.save()

    def get_content(self):
        if self.kind == Invite.EVENT:
            model = Event
        elif self.kind == Invite.EVENT_EDITOR:
            model = Event
        elif self.kind == Invite.ORGANIZATION_EDITOR:
            model = Organization
        elif self.kind == Invite.TRANSFER:
            model = BoughtItem
        else:
            raise ValueError('Unknown kind.')
        return model.objects.get(pk=self.content_id)


class CustomForm(models.Model):
    ATTENDEE = 'attendee'
    ORDER = 'order'
    HOUSING = 'housing'
    HOSTING = 'hosting'

    FORM_TYPE_CHOICES = (
        (ATTENDEE, _('Attendee')),
        (ORDER, _('Order')),
        (HOUSING, _('Housing')),
        (HOSTING, _('Hosting')),
    )
    form_type = models.CharField(max_length=8, choices=FORM_TYPE_CHOICES,
                                 help_text='Order forms will only display if "collect survey data" is checked in your event settings')
    event = models.ForeignKey(Event, related_name="forms")
    # TODO: Add fk/m2m to BoughtItem to limit people the form is
    # displayed to.
    name = models.CharField(max_length=50,
                            help_text="For organization purposes. This will not be displayed to attendees.")
    index = models.PositiveSmallIntegerField(default=0,
                                             help_text="Defines display order if you have multiple forms.")

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('index',)

    def get_fields(self):
        # Returns field definition dict that can be added to a form
        return SortedDict((
            (field.key, field.formfield())
            for field in self.fields.all()
        ))

    def get_data(self, related_obj):
        related_ct = ContentType.objects.get_for_model(related_obj)
        related_id = related_obj.pk
        entries = CustomFormEntry.objects.filter(
            related_ct=related_ct,
            related_id=related_id,
            form_field__form=self,
        )
        raw_data = {
            entry.form_field_id: entry.get_value()
            for entry in entries
        }
        return {
            field.key: raw_data[field.pk]
            for field in self.fields.all()
            if field.pk in raw_data
        }

    def save_data(self, cleaned_data, related_obj):
        related_ct = ContentType.objects.get_for_model(related_obj)
        related_id = related_obj.pk
        for field in self.fields.all():
            value = json.dumps(cleaned_data.get(field.key))
            CustomFormEntry.objects.update_or_create(
                related_ct=related_ct,
                related_id=related_id,
                form_field=field,
                defaults={'value': value},
            )


class CustomFormField(models.Model):
    TEXT = 'text'
    TEXTAREA = 'textarea'
    BOOLEAN = 'boolean'
    RADIO = 'radio'
    SELECT = 'select'
    CHECKBOXES = 'checkboxes'
    SELECT_MULTIPLE = 'select_multiple'

    CHOICE_TYPES = (RADIO, SELECT, CHECKBOXES, SELECT_MULTIPLE)

    FIELD_TYPE_CHOICES = (
        (TEXT, _('Text')),
        (TEXTAREA, _('Paragraph text')),
        (BOOLEAN, _('Checkbox')),
        (RADIO, _('Radio buttons')),
        (SELECT, _('Dropdown')),
        (CHECKBOXES, _('Multiple checkboxes')),
        (SELECT_MULTIPLE, _('Dropdown (Multiple)')),
    )
    field_type = models.CharField(max_length=15, choices=FIELD_TYPE_CHOICES, default=TEXT)

    form = models.ForeignKey(CustomForm, related_name='fields')
    name = models.CharField(max_length=255)
    default = models.CharField(max_length=255, blank=True)
    required = models.BooleanField(default=False)
    index = models.PositiveSmallIntegerField(default=0)
    # Choices are linebreak-separated values
    choices = models.TextField(help_text='Put each choice on its own line', default='', blank=True)
    help_text = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ('index',)

    @property
    def key(self):
        return "custom_{}_{}".format(self.form_id, self.pk)

    def formfield(self):
        kwargs = {
            'required': self.required,
            'initial': self.default,
            'label': self.name,
            'help_text': self.help_text,
        }
        if self.field_type in self.CHOICE_TYPES:
            choices = self.choices.splitlines()
            kwargs['choices'] = zip(choices, choices)

        if self.field_type == self.TEXT:
            field_class = forms.CharField
        elif self.field_type == self.TEXTAREA:
            field_class = forms.CharField
            kwargs['widget'] = forms.Textarea
        elif self.field_type == self.BOOLEAN:
            field_class = forms.BooleanField
        elif self.field_type == self.RADIO:
            field_class = forms.ChoiceField
            kwargs['widget'] = forms.RadioSelect
        elif self.field_type == self.SELECT:
            field_class = forms.ChoiceField
        elif self.field_type == self.CHECKBOXES:
            field_class = forms.MultipleChoiceField
            kwargs['widget'] = forms.CheckboxSelectMultiple
        elif self.field_type == self.SELECT_MULTIPLE:
            field_class = forms.MultipleChoiceField

        return field_class(**kwargs)


class CustomFormEntry(models.Model):
    related_ct = models.ForeignKey(ContentType)
    related_id = models.IntegerField()
    related_obj = GenericForeignKey('related_ct', 'related_id')

    form_field = models.ForeignKey(CustomFormField)
    value = models.TextField(blank=True)

    class Meta:
        unique_together = (('related_ct', 'related_id', 'form_field'),)

    def set_value(self, value):
        self.value = json.dumps(value)

    def get_value(self):
        try:
            return json.loads(self.value)
        except:
            return ''


class SavedReport(models.Model):
    ATTENDEE = 'attendee'
    ORDER = 'order'
    REPORT_TYPE_CHOICES = (
        (ATTENDEE, _('Attendee')),
        (ORDER, _('Order')),

    )
    report_type = models.CharField(max_length=8, choices=REPORT_TYPE_CHOICES)
    event = models.ForeignKey(Event)
    name = models.CharField(max_length=40)
    querystring = models.TextField()
