from django.contrib import messages
from django.http import HttpResponseRedirect, Http404
from django.views.generic import TemplateView, View

from brambling.models import Invite, Person
from brambling.forms.user import SignUpForm, FloppyAuthenticationForm
from brambling.utils.invites import get_invite_or_404, get_invite


class InviteAcceptView(TemplateView):
    template_name = 'brambling/invites/__base.html'

    def get(self, request, *args, **kwargs):
        try:
            self.invite = get_invite(request, code=kwargs['code'])
        except Invite.DoesNotExist:
            self.invite = None
        else:
            if request.user.is_authenticated() and request.user.email == self.invite.email:
                if request.user.confirmed_email != request.user.email:
                    request.user.confirmed_email = request.user.email
                    request.user.save()
                self.handle_invite()
                self.invite.delete()
                return HttpResponseRedirect(self.get_success_url())
        return super(InviteAcceptView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(InviteAcceptView, self).get_context_data(**kwargs)
        if self.invite:
            invited_person_exists = Person.objects.filter(email=self.invite.invite.email).exists()
            sender_display = self.invite.get_sender_display()
            invite = self.invite.invite
            content = self.invite.get_content()
        else:
            invited_person_exists = False
            sender_display = ''
            invite = None
            content = None
        context.update({
            'invite': invite,
            'content': content,
            'invited_person_exists': invited_person_exists,
            'sender_display': sender_display,
            'signup_form': SignUpForm(self.request),
            'login_form': FloppyAuthenticationForm(),
        })
        if self.invite:
            context['signup_form'].initial['email'] = self.invite.invite.email
            context['login_form'].initial['username'] = self.invite.invite.email
        return context

    def get_template_names(self):
        if self.invite and self.invite.accept_template:
            return [self.invite.accept_template]
        return super(InviteAcceptView, self).get_template_names()

    def get_success_url(self):
        return self.invite.post_accept_url()


class InviteSendView(View):
    def get(self, request, *args, **kwargs):
        self.invite = get_invite_or_404(request, kwargs['code'])
        if not self.invite.manage_allowed():
            raise Http404
        self.invite.send()
        messages.success(self.request, "Invitation sent to {}.".format(self.invite.invite.email))
        return HttpResponseRedirect(self.invite.post_manage_url())


class InviteDeleteView(View):
    def get(self, request, *args, **kwargs):
        self.invite = get_invite_or_404(request, kwargs['code'])
        if not self.invite.manage_allowed():
            raise Http404
        self.invite.invite.delete()
        messages.success(self.request, "Invitation for {} canceled.".format(self.invite.invite.email))
        return HttpResponseRedirect(self.invite.post_manage_url())
