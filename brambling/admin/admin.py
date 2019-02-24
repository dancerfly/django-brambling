from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count
from brambling.models import (
    Person,
    Event,
    DanceStyle,
    EnvironmentalFactor,
    HousingCategory,
    CustomForm,
    CustomFormField,
    Organization,
    Order,
    OrganizationMember,
    EventMember,
)
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
            ('first_name', 'last_name',),
            ('middle_name', 'name_order'),
        )}),
        ('Permissions', {'fields': (
            ('is_active', 'is_superuser',), 'user_permissions', 'groups'
        )}),
        ('Financial Transactions', {'fields': (
            ('stripe_customer_id', 'stripe_test_customer_id'),
        )})
    )

    search_fields = ('email', 'first_name', 'middle_name', 'last_name')
    ordering = ('-created',)

    def email_confirmed(self, obj):
        return obj.email == obj.confirmed_email
    email_confirmed.boolean = True


class OrganizationMemberInline(admin.TabularInline):
    model = OrganizationMember
    fields = ('person', 'role', 'created', 'last_modified')
    readonly_fields = ('created', 'last_modified')
    extra = 0
    raw_id_fields = ('person',)


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
        ("Stripe info", {
            'classes': ('grp-collapse grp-closed',),
            'fields': (
                ("stripe_user_id", "stripe_access_token"),
                ("stripe_refresh_token", "stripe_publishable_key"),
                ("stripe_test_user_id", "stripe_test_access_token"),
                ("stripe_test_refresh_token", "stripe_test_publishable_key"),
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
    filter_horizontal = ("dance_styles",)
    list_display = ('name', 'created', 'default_application_fee_percent', 'published_events', 'all_events')
    ordering = ('-created',)
    inlines = [OrganizationMemberInline]

    def get_queryset(self, request):
        qs = super(OrganizationAdmin, self).get_queryset(request)
        return qs.annotate(all_events=Count('event')).extra(select={
            'published_events': """
            SELECT COUNT(*) FROM brambling_event WHERE
            brambling_event.organization_id = brambling_organization.id AND
            brambling_event.is_published = '1'
            """
        })

    def all_events(self, obj):
        return obj.all_events

    def published_events(self, obj):
        return obj.published_events


class EventMemberInline(admin.TabularInline):
    model = EventMember
    fields = ('person', 'role', 'created', 'last_modified')
    readonly_fields = ('created', 'last_modified')
    extra = 0
    raw_id_fields = ('person',)


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
            'fields': ("organization",),
        }),
        ("Dancerfly Internal", {
            'classes': ('grp-collapse grp-closed',),
            'fields': ('is_frozen', 'application_fee_percent')
        }),
    )
    raw_id_fields = ('organization',)
    filter_horizontal = ("dance_styles",)
    radio_fields = {'api_type': admin.HORIZONTAL}
    list_display = ('name', 'organization', 'is_published', 'is_frozen', 'created', 'application_fee_percent')
    list_filter = ('organization', 'is_published', 'is_frozen')
    ordering = ('-created',)
    inlines = [EventMemberInline]

    def get_queryset(self, request):
        qs = super(EventAdmin, self).get_queryset(request)
        return qs.select_related('organization')


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
admin.site.register(HousingCategory)
admin.site.register(Order)
