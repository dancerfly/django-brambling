from django.db import models
from django.forms.models import inlineformset_factory
import floppyforms as forms

from brambling.models import Event, UserInfo, House, Item, ItemOption


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


class UserInfoForm(forms.ModelForm):
    formfield_callback = formfield_callback
    class Meta:
        model = UserInfo
        exclude = ('user',)


class HouseForm(forms.ModelForm):
    formfield_callback = formfield_callback
    class Meta:
        model = House
        exclude = ()


class ItemForm(forms.ModelForm):
    formfield_callback = formfield_callback

    def __init__(self, event, *args, **kwargs):
        self.event = event
        super(ItemForm, self).__init__(*args, **kwargs)

    def _post_clean(self):
        super(ItemForm, self)._post_clean()
        self.instance.event = self.event

    class Meta:
        model = Item
        exclude = ('event',)


ItemOptionFormSet = inlineformset_factory(Item, ItemOption, forms.ModelForm,
                                          exclude=(), extra=3,
                                          formfield_callback=formfield_callback)
