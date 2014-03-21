import floppyforms as forms

from brambling.models import Event, UserInfo, House


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
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
            'handle_housing': forms.CheckboxInput,
            'privacy': forms.RadioSelect,
            'editors': forms.SelectMultiple,
            'owner': forms.HiddenInput,
        }


class UserInfoForm(forms.ModelForm):
    class Meta:
        model = UserInfo
        exclude = ('user',)


class HouseForm(forms.ModelForm):
    class Meta:
        model = House
        exclude = ()
