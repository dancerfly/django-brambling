from django.db import models
from django.forms.models import inlineformset_factory
from django.utils.crypto import get_random_string
import floppyforms as forms

from brambling.models import (Event, Person, House, Item, ItemOption,
                              Discount, ItemDiscount)


FORMFIELD_OVERRIDES = {
    models.BooleanField: {'form_class': forms.BooleanField},
    models.CharField: {'form_class': forms.CharField},
    models.CommaSeparatedIntegerField: {'form_class': forms.CharField},
    models.DateField: {'form_class': forms.DateField},
    models.DateTimeField: {'form_class': forms.DateTimeField},
    models.DecimalField: {'form_class': forms.DecimalField},
    models.EmailField: {'form_class': forms.EmailField},
    models.FilePathField: {'form_class': forms.FilePathField},
    models.FloatField: {'form_class': forms.FloatField},
    models.IntegerField: {'form_class': forms.IntegerField},
    models.BigIntegerField: {'form_class': forms.IntegerField},
    models.IPAddressField: {'form_class': forms.IPAddressField},
    models.GenericIPAddressField: {'form_class': forms.GenericIPAddressField},
    models.NullBooleanField: {'form_class': forms.NullBooleanField},
    models.PositiveIntegerField: {'form_class': forms.IntegerField},
    models.PositiveSmallIntegerField: {'form_class': forms.IntegerField},
    models.SlugField: {'form_class': forms.SlugField},
    models.SmallIntegerField: {'form_class': forms.IntegerField},
    models.TextField: {'form_class': forms.CharField, 'widget': forms.Textarea},
    models.TimeField: {'form_class': forms.TimeField},
    models.URLField: {'form_class': forms.URLField},
    models.BinaryField: {'form_class': forms.CharField},

    models.FileField: {'form_class': forms.FileField},
    models.ImageField: {'form_class': forms.ImageField},

    models.ForeignKey: {'form_class': forms.ModelChoiceField},
    models.ManyToManyField: {'form_class': forms.ModelMultipleChoiceField},
    models.OneToOneField: {'form_class': forms.ModelChoiceField},
}


def formfield_callback(db_field, **kwargs):
    defaults = {'choices_form_class': forms.TypedChoiceField}
    defaults.update(FORMFIELD_OVERRIDES.get(db_field.__class__, {}))
    defaults.update(kwargs)
    return db_field.formfield(**defaults)


class EventForm(forms.ModelForm):
    formfield_callback = formfield_callback

    class Meta:
        model = Event
        exclude = ()


class PersonForm(forms.ModelForm):
    formfield_callback = formfield_callback

    class Meta:
        model = Person
        exclude = ('created_timestamp', 'last_login', 'groups',
                   'user_permissions', 'password', 'is_superuser')


class HouseForm(forms.ModelForm):
    formfield_callback = formfield_callback

    class Meta:
        model = House
        exclude = ()

    def __init__(self, person, *args, **kwargs):
        self.person = person
        super(HouseForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(HouseForm, self).save(commit)
        instance.residents.add(self.person)
        return instance


class ItemForm(forms.ModelForm):
    formfield_callback = formfield_callback

    class Meta:
        model = Item
        exclude = ('event',)

    def __init__(self, event, *args, **kwargs):
        self.event = event
        super(ItemForm, self).__init__(*args, **kwargs)

    def _post_clean(self):
        super(ItemForm, self)._post_clean()
        self.instance.event = self.event


ItemOptionFormSet = inlineformset_factory(Item, ItemOption, forms.ModelForm,
                                          exclude=(), extra=3,
                                          formfield_callback=formfield_callback)


class DiscountForm(forms.ModelForm):
    formfield_callback = formfield_callback
    autogenerate = forms.BooleanField()

    class Meta:
        model = Discount
        exclude = ('event', 'items')

    def __init__(self, event, *args, **kwargs):
        self.event = event
        super(DiscountForm, self).__init__(*args, **kwargs)
        if 'autogenerate' not in self.initial:
            self.initial['autogenerate'] = not self.instance.code
        self.fields['code'].required = False

    def _post_clean(self):
        super(DiscountForm, self)._post_clean()
        self.instance.event = self.event

    def save(self, commit=True):
        if (self.cleaned_data.get('autogenerate') or
                not self.cleaned_data.get('code')):
            code = get_random_string(6)
            while Discount.objects.filter(code=code).exists():
                code = get_random_string(6)
        self.instance.code = code
        return super(DiscountForm, self).save(commit)


ItemDiscountFormSet = inlineformset_factory(Discount, ItemDiscount,
                                            forms.ModelForm,
                                            exclude=(), extra=3,
                                            formfield_callback=formfield_callback)
