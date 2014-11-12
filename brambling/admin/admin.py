from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from brambling.models import Person
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
			('stripe_customer_id', 'default_card'),
			('dwolla_user_id', 'dwolla_access_token'),
		)})
	)

	search_fields = ('email',)
	ordering = ('-created_timestamp',)


admin.site.register(Person, PersonAdmin)
