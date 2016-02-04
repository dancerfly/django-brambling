from django.forms import BaseFormSet

import floppyforms as forms

from brambling.utils.invites import (
    get_invite_class,
    OrganizationOwnerInvite,
    OrganizationEditInvite,
    OrganizationViewInvite,
    EventEditInvite,
    EventViewInvite,
)


class BaseInviteFormSet(BaseFormSet):
    def __init__(self, request, content, *args, **kwargs):
        self.request = request
        self.content = content
        super(BaseInviteFormSet, self).__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        kwargs['request'] = self.request
        kwargs['content'] = self.content
        return super(BaseInviteFormSet, self)._construct_form(i, **kwargs)

    @property
    def empty_form(self):
        form = self.form(
            auto_id=self.auto_id,
            prefix=self.add_prefix('__prefix__'),
            empty_permitted=True,
            request=self.request,
            content=self.content,
        )
        self.add_fields(form, None)
        return form

    def save(self):
        for form in self:
            form.save()


class BaseInviteForm(forms.Form):
    email = forms.EmailField()
    kind = forms.ChoiceField()
    choices = ()

    def __init__(self, request, content, *args, **kwargs):
        super(BaseInviteForm, self).__init__(*args, **kwargs)
        self.request = request
        self.content = content
        self.fields['kind'].choices = self.choices

    def save(self):
        invite_class = get_invite_class(self.cleaned_data['kind'])
        invite, created = invite_class.get_or_create(
            request=self.request,
            email=self.cleaned_data['email'],
            content=self.content,
        )
        if created:
            invite.send()


class EventAdminInviteForm(BaseInviteForm):
    choices = (
        (EventEditInvite.slug, EventEditInvite.verbose_name),
        (EventViewInvite.slug, EventViewInvite.verbose_name),
    )


class OrganizationAdminInviteForm(BaseInviteForm):
    choices = (
        (OrganizationOwnerInvite.slug, OrganizationOwnerInvite.verbose_name),
        (OrganizationEditInvite.slug, OrganizationEditInvite.verbose_name),
        (OrganizationViewInvite.slug, OrganizationViewInvite.verbose_name),
    )
