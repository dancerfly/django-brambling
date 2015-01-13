from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from brambling.models import Person, Event
from brambling.admin.forms import PersonChangeForm, PersonCreationForm


class PersonAdmin(UserAdmin):
    "https://docs.djangoproject.com/en/1.7/topics/auth/customizing/#a-full-example"

    form = PersonChangeForm
    add_form = PersonCreationForm
    list_display = ('email', 'is_active',)
    list_filter = ('is_active',)

    add_fieldsets = (
        (None, {
            'fields': (('email', 'password1', 'password2'), tuple(Person.REQUIRED_FIELDS))
        }),
    )

    fieldsets = (
        (None, {'fields': (('email', 'confirmed_email',), 'password')}),
        ('Personal', {'fields': (
            ('given_name', 'surname',), ('middle_name', 'name_order'),
            ('phone',)
        )}),
        ('Permissions', {'fields': (
            ('is_active', 'is_superuser',), 'user_permissions', 'groups'
        )}),
        ('Registration Settings', {'fields': (
            'dietary_restrictions',
            ('ef_cause', 'ef_avoid'),
            'person_prefer',
            'person_avoid',
            'housing_prefer',
            'other_needs',
            'dance_styles',
        )}),
        ('Financial Transactions', {'fields': (
            ('stripe_customer_id', 'stripe_test_customer_id', 'default_card'),
            ('dwolla_user_id', 'dwolla_access_token'),
            ('dwolla_test_user_id', 'dwolla_test_access_token'),
        )})
    )

    search_fields = ('email',)
    ordering = ('-created_timestamp',)


class EventAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'api_type'),
        }),
        ("Details", {
            'classes': ('grp-collapse grp-closed',),
            'fields': (
                ('name', 'slug'),
                ('has_dances', 'has_classes'),
                'privacy', 'is_published',
                ('website_url', 'banner_image'),
                'description',
                ('city', 'state_or_province'),
                'country',
                'dance_styles',
                'currency',
            ),
        }),
        ("Dates", {
            'classes': ('grp-collapse grp-closed',),
            'fields': (
                'timezone', 'dates',
                ('start_time', 'end_time'),
                'housing_dates'
            )
        }),
        ("Checkout", {
            'classes': ('grp-collapse grp-closed',),
            'fields': (
                ('collect_housing_data', 'collect_survey_data'),
                'liability_waiver', 'cart_timeout', 'housing_dates'
            )
        }),
        ("Permissions", {
            'classes': ('grp-collapse grp-closed',),
            'fields': ("owner", "editors"),
        }),
        ("Payment Methods", {
            'classes': ('grp-collapse grp-closed',),
            'fields': (
                ("dwolla_user_id", "dwolla_access_token"),
                ("stripe_user_id", "stripe_access_token"),
                ("stripe_refresh_token", "stripe_publishable_key"),
                ("dwolla_test_user_id", "dwolla_test_access_token"),
                ("stripe_test_user_id", "stripe_test_access_token"),
                ("stripe_test_refresh_token", "stripe_test_publishable_key"),
                "check_payment_allowed",
                ("check_payable_to", "check_postmark_cutoff"),
                "check_recipient",
                "check_address", "check_address_2",
                ("check_city", "check_state_or_province"),
                ("check_zip", "check_country"),
            )
        }),
        ("Dancerfly Internal", {
            'classes': ('grp-collapse grp-closed',),
            'fields': ('is_frozen', 'application_fee_percent')
        }),
    )
    raw_id_fields = ('owner',)
    filter_horizontal = ("dance_styles", "dates", "housing_dates", "editors")
    radio_fields = {'api_type': admin.HORIZONTAL}


admin.site.register(Person, PersonAdmin)
admin.site.register(Event, EventAdmin)
