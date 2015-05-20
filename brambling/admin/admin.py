from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from brambling.models import (Person, Event, DanceStyle,
                              EnvironmentalFactor, DietaryRestriction,
                              HousingCategory, CustomForm, CustomFormField,
                              Organization)
from brambling.admin.forms import PersonChangeForm, PersonCreationForm


class PersonAdmin(UserAdmin):
    "https://docs.djangoproject.com/en/1.7/topics/auth/customizing/#a-full-example"

    form = PersonChangeForm
    add_form = PersonCreationForm
    list_display = ('get_full_name', 'email', 'email_confirmed', 'is_active', 'created')
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
            ('stripe_customer_id', 'stripe_test_customer_id'),
            "dwolla_user_id",
            ("dwolla_access_token", "dwolla_access_token_expires"),
            ("dwolla_refresh_token", "dwolla_refresh_token_expires"),
            "dwolla_test_user_id",
            ("dwolla_test_access_token", "dwolla_test_access_token_expires"),
            ("dwolla_test_refresh_token", "dwolla_test_refresh_token_expires"),
        )})
    )

    search_fields = ('email', 'given_name', 'middle_name', 'surname')
    ordering = ('-created',)

    def email_confirmed(self, obj):
        return obj.email == obj.confirmed_email
    email_confirmed.boolean = True


class OrganizationAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('name', 'slug'),
        }),
        ("Details", {
            'classes': ('grp-collapse grp-closed',),
            'fields': (
                'description',
                'website_url',
                'facebook_url',
                'banner_image',
                ('city', 'state_or_province'),
                'country',
                'dance_styles',
            ),
        }),
        ("Permissions", {
            'classes': ('grp-collapse grp-closed',),
            'fields': ("owner", "editors"),
        }),
        ("Event defaults", {
            'classes': ('grp-collapse grp-closed',),
            'fields': (
                'default_event_city',
                'default_event_state_or_province',
                'default_event_country',
                'default_event_dance_styles',
                'default_event_timezone',
                'default_event_currency',
            ),
        }),
        ("Stripe info", {
            'classes': ('grp-collapse grp-closed',),
            'fields': (
                ("stripe_user_id", "stripe_access_token"),
                ("stripe_refresh_token", "stripe_publishable_key"),
                ("stripe_test_user_id", "stripe_test_access_token"),
                ("stripe_test_refresh_token", "stripe_test_publishable_key"),
            )
        }),
        ("Dwolla info", {
            'classes': ('grp-collapse grp-closed',),
            'fields': (
                "dwolla_user_id",
                ("dwolla_access_token", "dwolla_access_token_expires"),
                ("dwolla_refresh_token", "dwolla_refresh_token_expires"),
                "dwolla_test_user_id",
                ("dwolla_test_access_token", "dwolla_test_access_token_expires"),
                ("dwolla_test_refresh_token", "dwolla_test_refresh_token_expires"),
            )
        }),
        ("Check info", {
            'classes': ('grp-collapse grp-closed',),
            'fields': (
                "check_payment_allowed",
                "check_payable_to",
                "check_recipient",
                "check_address", "check_address_2",
                ("check_city", "check_state_or_province"),
                ("check_zip", "check_country"),
            )
        }),
        ("Dancerfly Internal", {
            'classes': ('grp-collapse grp-closed',),
            'fields': ('default_application_fee_percent',)
        }),
    )
    raw_id_fields = ('owner',)
    filter_horizontal = ("dance_styles", "default_event_dance_styles", "editors")
    list_display = ('name', 'created')
    ordering = ('-created',)


class EventAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'api_type'),
        }),
        ("Details", {
            'classes': ('grp-collapse grp-closed',),
            'fields': (
                ('has_dances', 'has_classes'),
                'privacy', 'is_published',
                ('website_url', 'banner_image'),
                'description',
                ('city', 'state_or_province'),
                'country',
                'dance_styles',
                'currency',
                'check_postmark_cutoff',
            ),
        }),
        ("Dates", {
            'classes': ('grp-collapse grp-closed',),
            'fields': (
                'timezone',
                ('start_date', 'end_date'),
                ('start_time', 'end_time'),
            )
        }),
        ("Checkout", {
            'classes': ('grp-collapse grp-closed',),
            'fields': (
                ('collect_housing_data', 'collect_survey_data'),
                'liability_waiver', 'cart_timeout',
            )
        }),
        ("Permissions", {
            'classes': ('grp-collapse grp-closed',),
            'fields': ("organization", "additional_editors"),
        }),
        ("Dancerfly Internal", {
            'classes': ('grp-collapse grp-closed',),
            'fields': ('is_frozen', 'application_fee_percent')
        }),
    )
    raw_id_fields = ('organization',)
    filter_horizontal = ("dance_styles", "additional_editors")
    radio_fields = {'api_type': admin.HORIZONTAL}
    list_display = ('name', 'created')
    ordering = ('-created',)


class CustomFormFieldInline(admin.TabularInline):
    model = CustomFormField
    extra = 0
    min_num = 1
    sortable_field_name = "index"


class CustomFormAdmin(admin.ModelAdmin):
    inlines = [CustomFormFieldInline]
    radio_fields = {'form_type': admin.HORIZONTAL}
    raw_id_fields = ('event',)
    fields = ('name', 'form_type', 'event', 'index')
    autocomplete_lookup_fields = {
        'fk': ('event',),
    }


admin.site.register(Person, PersonAdmin)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(CustomForm, CustomFormAdmin)
admin.site.register(DanceStyle)
admin.site.register(EnvironmentalFactor)
admin.site.register(DietaryRestriction)
admin.site.register(HousingCategory)
