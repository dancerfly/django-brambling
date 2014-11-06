from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from brambling.models import Person


# Custom UserAdmin (see: https://docs.djangoproject.com/en/1.7/topics/auth/customizing/#a-full-example)

class PersonCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = Person
        fields = (Person.USERNAME_FIELD,) + tuple(Person.REQUIRED_FIELDS)

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user



class PersonChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = Person
        fields = ('email', 'password', 'is_active',)

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class PersonAdmin(UserAdmin):
    form = PersonChangeForm
    add_form = PersonCreationForm
    list_display = ('email', 'is_active',)
    list_filter = ('is_active',)

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
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
            ('person_prefer', 'person_avoid'),
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
