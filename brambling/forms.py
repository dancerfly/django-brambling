import floppyforms as forms

from brambling.models import Event


class EventForm(forms.ModelForm):
    category = Event._meta.get_field('category'
                                     ).formfield(widget=forms.RadioSelect)
    privacy = Event._meta.get_field('privacy'
                                    ).formfield(widget=forms.RadioSelect)

    class Meta:
        model = Event
        exclude = ('owner',)
        widgets = {
            'name': forms.TextInput,
            'slug': forms.SlugInput,
            'tagline': forms.TextInput,
            'city': forms.TextInput,
            'state_or_province': forms.TextInput,
            'timezone': forms.TextInput,
            'currency': forms.TextInput,
            'start_date': forms.DateInput,
            'end_date': forms.DateInput,
            'category': forms.RadioSelect,
            'handle_housing': forms.CheckboxInput,
            'privacy': forms.RadioSelect,
            'editors': forms.SelectMultiple,
        }
