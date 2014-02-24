from django import forms

from brambling.models import Event


class EventForm(forms.ModelForm):
    category = Event._meta.get_field('category'
                                     ).formfield(widget=forms.RadioSelect)
    privacy = Event._meta.get_field('privacy'
                                    ).formfield(widget=forms.RadioSelect)

    class Meta:
        model = Event
        exclude = ('owner',)
