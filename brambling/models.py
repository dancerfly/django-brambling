# encoding: utf8
from datetime import timedelta
import itertools
import operator

from django.conf import settings
from django.contrib.auth.models import (AbstractBaseUser, PermissionsMixin,
                                        BaseUserManager)
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.core.validators import (MaxValueValidator, MinValueValidator,
                                    RegexValidator)
from django.dispatch import receiver
from django.db import models
from django.db.models import signals
from django.template.defaultfilters import date, striptags
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField


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
        return self.NAME_ORDER_PATTERNS[self.name_order].format(**name_dict)

    def get_short_name(self):
        return self.given_name

    class Meta:
        abstract = True


class DanceStyle(models.Model):
    name = models.CharField(max_length=30, unique=True)

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
    if app_config.name == 'brambling':
        if not DanceStyle.objects.exists():
            if kwargs.get('verbosity') >= 2:
                print("Creating default dance styles")
            DanceStyle.objects.bulk_create([
                DanceStyle(name=name)
                for name in DEFAULT_DANCE_STYLES
            ])
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

    PRIVACY_CHOICES = (
        (PUBLIC, _("List publicly")),
        (LINK, _("Visible to anyone with the link")),
    )
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50,
                            validators=[RegexValidator("[a-z0-9-]+")],
                            help_text="URL-friendly version of the event name."
                                      " Dashes, 0-9, and lower-case a-z only.",
                            unique=True)
    description = models.TextField(blank=True)
    website_url = models.URLField(blank=True)
    logo_image = models.ImageField(blank=True)
    banner_image = models.ImageField(blank=True)
    city = models.CharField(max_length=50)
    state_or_province = models.CharField(max_length=50)
    country = CountryField(default='US')
    timezone = models.CharField(max_length=40, default='UTC')
    currency = models.CharField(max_length=10, default='USD')

    dates = models.ManyToManyField(Date, related_name='event_dates')
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    housing_dates = models.ManyToManyField(Date, blank=True, null=True,
                                           related_name='event_housing_dates')

    dance_styles = models.ManyToManyField(DanceStyle, blank=True)
    has_dances = models.BooleanField(verbose_name="Is a dance / Has dance(s)", default=False)
    has_classes = models.BooleanField(verbose_name="Is a class / Has class(es)", default=False)
    liability_waiver = models.TextField(default=_("I hereby release {event}, its officers, and its employees from all "
                                                  "liability of injury, loss, or damage to personal property associated "
                                                  "with this event. I acknowledge that I understand the content of this "
                                                  "document. I am aware that it is legally binding and I accept it out "
                                                  "of my own free will."), help_text=_("'{event}' will be automatically replaced with your event name when users are presented with the waiver."))

    privacy = models.CharField(max_length=7, choices=PRIVACY_CHOICES,
                               default=PUBLIC, help_text="Who can view this event.")
    is_published = models.BooleanField(default=False)
    # If an event is "frozen", it can no longer be edited or unpublished.
    is_frozen = models.BooleanField(default=False)

    owner = models.ForeignKey('Person',
                              related_name='owner_events')
    editors = models.ManyToManyField('Person',
                                     related_name='editor_events',
                                     blank=True, null=True)

    last_modified = models.DateTimeField(auto_now=True)

    collect_housing_data = models.BooleanField(default=True)
    collect_survey_data = models.BooleanField(default=True)

    # Time in minutes.
    cart_timeout = models.PositiveSmallIntegerField(default=15,
                                                    help_text="Minutes before a user's cart expires.")

    # These are obtained with Stripe Connect via Oauth.
    stripe_user_id = models.CharField(max_length=32, blank=True, default='')
    stripe_access_token = models.CharField(max_length=32, blank=True, default='')
    stripe_refresh_token = models.CharField(max_length=32, blank=True, default='')
    stripe_publishable_key = models.CharField(max_length=32, blank=True, default='')

    # Token obtained via OAuth.
    dwolla_user_id = models.CharField(max_length=20, blank=True, default='')
    dwolla_access_token = models.CharField(max_length=50, blank=True, default='')

    def __unicode__(self):
        return smart_text(self.name)

    def get_absolute_url(self):
        return reverse('brambling_event_root', kwargs={'event_slug': self.slug})

    def get_liability_waiver(self):
        return self.liability_waiver.format(event=self.name)

    def editable_by(self, user):
        return (user.is_authenticated() and user.is_active and
                (user.is_superuser or user.pk == self.owner_id or
                 self.editors.filter(pk=user.pk).exists()))

    def viewable_by(self, user):
        if not user.is_authenticated() or not user.is_active:
            return False

        if not self.is_published and not self.editable_by(user):
            return False

        return True

    def can_be_published(self):
        # See https://github.com/littleweaver/django-brambling/issues/150
        # At least one pass / class must exist before the event can be published.
        pass_class_count = ItemOption.objects.filter(item__event=self, item__category__in=(Item.CLASS, Item.PASS)).count()
        return pass_class_count >= 1

    def uses_stripe(self):
        return bool(self.stripe_user_id)

    def uses_dwolla(self):
        return bool(self.dwolla_user_id)

    def get_invites(self):
        return Invite.objects.filter(kind=Invite.EDITOR,
                                     content_id=self.pk)


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
    description = models.TextField(blank=True)
    category = models.CharField(max_length=7, choices=CATEGORIES)
    event = models.ForeignKey(Event, related_name='items')

    created_timestamp = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return smart_text(self.name)


class ItemImage(models.Model):
    item = models.ForeignKey(Item, related_name='images')
    order = models.PositiveSmallIntegerField()
    image = models.ImageField()


class ItemOption(models.Model):
    item = models.ForeignKey(Item, related_name='options')
    name = models.CharField(max_length=30)
    price = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    total_number = models.PositiveSmallIntegerField(blank=True, null=True, help_text="Leave blank for unlimited.")
    available_start = models.DateTimeField(default=timezone.now)
    available_end = models.DateTimeField()
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ('order',)

    def __unicode__(self):
        return smart_text(self.name)

    @property
    def remaining(self):
        if not hasattr(self, 'taken'):
            self.taken = self.boughtitem_set.exclude(status=BoughtItem.REFUNDED).count()
        return self.total_number - self.taken


class Discount(models.Model):
    CODE_REGEX = '[0-9A-Za-z \'"~]+'
    PERCENT = 'percent'
    FLAT = 'flat'

    TYPE_CHOICES = (
        (FLAT, _('Flat')),
        (PERCENT, _('Percent')),
    )
    name = models.CharField(max_length=40)
    code = models.CharField(max_length=20, validators=[RegexValidator(CODE_REGEX)],
                            help_text="Allowed characters: 0-9, a-z, A-Z, space, and '\"~")
    item_options = models.ManyToManyField(ItemOption)
    available_start = models.DateTimeField(default=timezone.now)
    available_end = models.DateTimeField()
    discount_type = models.CharField(max_length=7,
                                     choices=TYPE_CHOICES,
                                     default=FLAT)
    amount = models.DecimalField(max_digits=5, decimal_places=2,
                                 validators=[MinValueValidator(0)])
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
                            last_login=now, created_timestamp=now, **extra_fields)
        person.set_password(password)
        person.save(using=self._db)
        return person

    def create_user(self, email, password=None, **extra_fields):
        return self._create_user(email, password, False, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        return self._create_user(email, password, True, **extra_fields)


class Person(AbstractNamedModel, AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=254, unique=True)
    confirmed_email = models.EmailField(max_length=254)
    phone = models.CharField(max_length=50, blank=True)
    home = models.ForeignKey('Home', blank=True, null=True,
                             related_name='residents')

    created_timestamp = models.DateTimeField(default=timezone.now, editable=False)

    ### Start custom user requirements
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['given_name', 'surname']

    @property
    def is_staff(self):
        return self.is_superuser

    is_active = models.BooleanField(default=True)

    objects = PersonManager()
    ### End custom user requirements

    dietary_restrictions = models.ManyToManyField(DietaryRestriction,
                                                  blank=True,
                                                  null=True)

    ef_cause = models.ManyToManyField(EnvironmentalFactor,
                                      related_name='person_cause',
                                      blank=True,
                                      null=True,
                                      verbose_name="People around me may be exposed to")

    ef_avoid = models.ManyToManyField(EnvironmentalFactor,
                                      related_name='person_avoid',
                                      blank=True,
                                      null=True,
                                      verbose_name="I can't/don't want to be around")

    person_prefer = models.TextField(blank=True,
                                     verbose_name="I need to be placed with")

    person_avoid = models.TextField(blank=True,
                                    verbose_name="I do not want to be around")

    housing_prefer = models.ManyToManyField(HousingCategory,
                                            related_name='preferred_by',
                                            blank=True,
                                            null=True,
                                            verbose_name="I prefer to stay somewhere that is (a/an)")

    other_needs = models.TextField(blank=True)

    dance_styles = models.ManyToManyField(DanceStyle, blank=True)

    # Stripe-related fields
    stripe_customer_id = models.CharField(max_length=36, blank=True)
    default_card = models.OneToOneField('CreditCard', blank=True, null=True,
                                        related_name='default_for',
                                        on_delete=models.SET_NULL)
    # Token obtained via OAuth.
    dwolla_user_id = models.CharField(max_length=20, blank=True, default='')
    dwolla_access_token = models.CharField(max_length=50, blank=True, default='')

    # Internal tracking
    modified_directly = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('person')
        verbose_name_plural = _('people')

    def __unicode__(self):
        return self.get_full_name()


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
    person = models.ForeignKey(Person, related_name='cards', blank=True, null=True)
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


class Order(models.Model):
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
    person = models.ForeignKey(Person, blank=True, null=True)
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
    send_flyers_city = models.CharField(max_length=50, verbose_name='city', blank=True)
    send_flyers_state_or_province = models.CharField(max_length=50, verbose_name='state or province', blank=True)
    send_flyers_country = CountryField(verbose_name='country', blank=True)

    providing_housing = models.BooleanField(default=False)

    checked_out = models.BooleanField(default=False)

    class Meta:
        unique_together = ('event', 'code')

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
            ).exclude(status=BoughtItem.REFUNDED)
            BoughtItemDiscount.objects.bulk_create([
                BoughtItemDiscount(discount=discount,
                                   bought_item=bought_item)
                for bought_item in bought_items
            ])
        return created

    def add_to_cart(self, item_option):
        if self.cart_is_expired():
            self.delete_cart()
        bought_item = BoughtItem.objects.create(
            item_option=item_option,
            order=self,
            status=BoughtItem.RESERVED
        )
        discounts = self.discounts.filter(
            discount__item_options=item_option
        ).select_related('discount').distinct()
        if discounts:
            BoughtItemDiscount.objects.bulk_create([
                BoughtItemDiscount(discount=discount.discount,
                                   bought_item=bought_item)
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

    def mark_cart_paid(self):
        self.bought_items.filter(
            status__in=(BoughtItem.RESERVED, BoughtItem.UNPAID)
        ).update(status=BoughtItem.PAID)
        if self.cart_start_time is not None:
            self.cart_start_time = None
        self.checked_out = True
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

    def get_summary_data(self):
        payments = self.payments.order_by('timestamp')
        bought_items_qs = self.bought_items.select_related('item_option', 'attendee', 'event_pass_for', 'discounts', 'discounts__discount').order_by('attendee', 'added')
        attendees = []
        bought_items = []
        for k, g in itertools.groupby(bought_items_qs, operator.attrgetter('attendee')):
            items = [item.get_summary_data() for item in g]
            bought_items.extend(items)

            gross_cost = sum((item['gross_cost'] for item in items))
            gross_payments = sum((item['gross_payments'] for item in items))
            total_savings = sum((item['total_savings'] for item in items))
            total_refunds = sum((item['total_refunds'] for item in items))
            net_cost = gross_cost - total_refunds - total_savings
            net_payments = gross_payments - total_refunds
            net_balance = net_cost - net_payments
            attendees.append({
                'attendee': k,
                'bought_items': items,
                'gross_cost': gross_cost,
                'gross_payments': gross_payments,
                'total_savings': total_savings,
                'total_refunds': total_refunds,
                'net_cost': net_cost,
                'net_payments': net_payments,
                'net_balance': net_balance,
            })

        gross_cost = sum((item.item_option.price for item in bought_items_qs))
        gross_payments = sum((payment.amount for payment in payments))
        total_savings = sum((attendee['total_savings']
                             for attendee in attendees))
        total_refunds = sum((attendee['total_refunds']
                             for attendee in attendees))
        net_cost = gross_cost - total_refunds - total_savings
        net_payments = gross_payments - total_refunds
        net_balance = net_cost - net_payments
        return {
            'attendees': attendees,
            'bought_items': bought_items,
            'payments': payments,
            'refunds': self.refunds.order_by('timestamp'),
            'gross_cost': gross_cost,
            'gross_payments': gross_payments,
            'total_savings': total_savings,
            'total_refunds': total_refunds,
            'net_cost': net_cost,
            'net_payments': net_payments,
            'net_balance': net_balance,
        }

    def get_eventhousing(self):
        # Workaround for DNE exceptions on nonexistant reverse relations.
        if not hasattr(self, '_eventhousing'):
            try:
                self._eventhousing = self.eventhousing
            except EventHousing.DoesNotExist:
                self._eventhousing = None
        return self._eventhousing


class Payment(models.Model):
    STRIPE = 'stripe'
    DWOLLA = 'dwolla'
    CASH = 'cash'
    CHECK = 'check'
    FAKE = 'fake'

    METHOD_CHOICES = (
        (STRIPE, 'Stripe'),
        (DWOLLA, 'Dwolla'),
        (CASH, 'Cash'),
        (CHECK, 'Check'),
        (FAKE, 'Fake')
    )
    order = models.ForeignKey('Order', related_name='payments')
    amount = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0.01)])
    timestamp = models.DateTimeField(default=timezone.now)
    method = models.CharField(max_length=6, choices=METHOD_CHOICES)
    remote_id = models.CharField(max_length=40, blank=True)
    card = models.ForeignKey('CreditCard', blank=True, null=True)


class SubPayment(models.Model):
    """
    Represents a portion of a payment assigned to a particular bought item.
    """
    payment = models.ForeignKey(Payment, related_name='subpayments')
    bought_item = models.ForeignKey('BoughtItem', related_name='subpayments')
    amount = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        unique_together = ('payment', 'bought_item')


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
    order = models.ForeignKey(Order, related_name='bought_items')
    added = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=8,
                              choices=STATUS_CHOICES,
                              default=UNPAID)
    # BoughtItem has a single attendee, but attendee can have
    # more than one BoughtItem. Basic example: Attendee can
    # have more than one class. Or, hypothetically, merch bought
    # by a single person could be assigned to multiple attendees.
    attendee = models.ForeignKey('Attendee', blank=True, null=True,
                                 related_name='bought_items', on_delete=models.SET_NULL)
    payments = models.ManyToManyField(Payment, through=SubPayment)

    def __unicode__(self):
        return u"{} – {} ({})".format(self.item_option.name,
                                      self.order.person.get_full_name(),
                                      self.pk)

    def get_summary_data(self):
        gross_cost = self.item_option.price
        payments = self.subpayments.order_by('payment__timestamp')
        discounts = self.discounts.order_by('timestamp')
        refunds = self.refunds.order_by('timestamp')
        total_savings = sum((discount.savings() for discount in discounts))
        gross_payments = sum((payment.amount for payment in payments))
        total_refunds = sum((refund.amount for refund in refunds))
        net_cost = gross_cost - total_refunds - total_savings
        net_payments = gross_payments - total_refunds
        net_balance = net_cost - net_payments

        return {
            'bought_item': self,
            'payments': payments,
            'discounts': discounts,
            'refunds': refunds,
            'gross_cost': gross_cost,
            'gross_payments': gross_payments,
            'total_savings': total_savings,
            'total_refunds': total_refunds,
            'net_cost': net_cost,
            'net_payments': net_payments,
            'net_balance': net_balance,
            'uses_dwolla': any((payment.payment.method == Payment.DWOLLA
                                for payment in payments)),
        }


class OrderDiscount(models.Model):
    """Tracks whether a person has entered a code for an event."""
    discount = models.ForeignKey(Discount)
    order = models.ForeignKey(Order, related_name='discounts')
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('order', 'discount')


class BoughtItemDiscount(models.Model):
    """"Tracks whether an item has had a discount applied to it."""
    discount = models.ForeignKey(Discount)
    bought_item = models.ForeignKey(BoughtItem, related_name='discounts')
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('bought_item', 'discount')

    def savings(self):
        discount = self.discount
        item_option = self.bought_item.item_option
        return min(discount.amount
                   if discount.discount_type == Discount.FLAT
                   else discount.amount / 100 * item_option.price,
                   item_option.price)


class Refund(models.Model):
    order = models.ForeignKey('Order', related_name='refunds')
    issuer = models.ForeignKey('Person')
    bought_item = models.ForeignKey(BoughtItem, related_name='refunds')
    timestamp = models.DateTimeField(default=timezone.now)
    amount = models.DecimalField(max_digits=5, decimal_places=2)


class SubRefund(models.Model):
    STRIPE = Payment.STRIPE
    DWOLLA = Payment.DWOLLA
    METHOD_CHOICES = Payment.METHOD_CHOICES

    refund = models.ForeignKey(Refund)
    subpayment = models.ForeignKey(SubPayment, related_name='refunds')
    amount = models.DecimalField(max_digits=5, decimal_places=2)
    method = models.CharField(max_length=6, choices=METHOD_CHOICES)
    remote_id = models.CharField(max_length=40, blank=True)


class Attendee(AbstractNamedModel):
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
    order = models.ForeignKey(Order, related_name='attendees')
    person = models.ForeignKey(Person, blank=True, null=True)
    person_confirmed = models.BooleanField(default=False)
    event_pass = models.OneToOneField(BoughtItem, related_name='event_pass_for')

    # Basic data - always required for attendees.
    basic_completed = models.BooleanField(default=False)
    email = models.EmailField(max_length=254)
    phone = models.CharField(max_length=50, blank=True, help_text="Required if requesting housing")
    liability_waiver = models.BooleanField(default=False, help_text="Must be agreed to by the attendee themselves.")
    photo_consent = models.BooleanField(default=False, verbose_name='I consent to have my photo taken at this event.')
    housing_status = models.CharField(max_length=4, choices=HOUSING_STATUS_CHOICES,
                                      default=HAVE, verbose_name='housing status')

    # Housing information - all optional.
    housing_completed = models.BooleanField(default=False)
    nights = models.ManyToManyField(Date, blank=True, null=True)
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

    def __unicode__(self):
        return self.get_full_name()

    def get_groupable_items(self):
        return self.bought_items.order_by('item_option__item', 'item_option__order', '-added')


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

    def get_invites(self):
        return Invite.objects.filter(kind=Invite.HOME,
                                     content_id=self.pk)


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
    city = models.CharField(max_length=50)
    state_or_province = models.CharField(max_length=50)
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


class InviteManager(models.Manager):
    def get_or_create_invite(self, email, user, kind, content_id):
        while True:
            code = get_random_string(
                length=20,
                allowed_chars='abcdefghijklmnopqrstuvwxyz'
                              'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-~'
            )
            if not Invite.objects.filter(code=code):
                break
        defaults = {
            'user': user,
            'code': code,
        }
        return self.get_or_create(email=email, content_id=content_id, kind=kind, defaults=defaults)


class Invite(models.Model):
    HOME = 'home'
    EDITOR = 'editor'
    KIND_CHOICES = (
        (HOME, _("Home")),
        (EDITOR, _("Editor")),
    )

    objects = InviteManager()
    code = models.CharField(max_length=20, unique=True)
    email = models.EmailField()
    #: User who sent the invitation.
    user = models.ForeignKey(Person)
    is_sent = models.BooleanField(default=False)
    kind = models.CharField(max_length=6, choices=KIND_CHOICES)
    content_id = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('email', 'content_id', 'kind'),)

    def send(self, site, body_template_name='brambling/mail/invite_{kind}_body.html',
             subject_template_name='brambling/mail/invite_{kind}_subject.html',
             content=None, secure=False):
        context = {
            'invite': self,
            'site': site,
            'protocol': 'https' if secure else 'http',
        }
        if content is not None:
            context['content'] = content
        body = render_to_string(
            body_template_name.format(kind=self.kind),
            context
        )
        subject = render_to_string(
            subject_template_name.format(kind=self.kind),
            context
        )

        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())

        send_mail(
            subject=subject,
            message=striptags(body),
            html_message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.email],
        )
        self.is_sent = True
        self.save()
