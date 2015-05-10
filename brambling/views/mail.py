from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import Http404, HttpResponse
from django.views.generic import View

from brambling.mail import (ConfirmationMailer, OrderReceiptMailer,
                            OrderAlertMailer, InviteMailer)
from brambling.models import Order, Invite


class PreviewView(View):
    mailer = None

    def get_mailer_kwargs(self):
        return {
            'site': get_current_site(self.request),
            'secure': self.request.is_secure(),
        }

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            raise Http404
        mailer = self.mailer(**self.get_mailer_kwargs())
        if request.GET.get('email'):
            try:
                validate_email(request.GET['email'])
            except ValidationError:
                return HttpResponse('Invalid email address')
            else:
                mailer.send([request.GET['email']])
                return HttpResponse('Email sent to ' + request.GET['email'])
        return mailer.render_to_response(inlined=request.GET.get('inlined'),
                                         plaintext=request.GET.get('plaintext'))


class ConfirmationPreviewView(PreviewView):
    mailer = ConfirmationMailer

    def get_mailer_kwargs(self):
        kwargs = super(ConfirmationPreviewView, self).get_mailer_kwargs()
        kwargs['person'] = self.request.user
        return kwargs


class OrderReceiptPreviewView(PreviewView):
    mailer = OrderReceiptMailer

    def get_mailer_kwargs(self):
        kwargs = super(OrderReceiptPreviewView, self).get_mailer_kwargs()
        kwargs['order'] = Order.objects.order_by('?')[0]
        kwargs['summary_data'] = kwargs['order'].get_summary_data()
        return kwargs


class OrderAlertPreviewView(PreviewView):
    mailer = OrderAlertMailer

    def get_mailer_kwargs(self):
        kwargs = super(OrderAlertPreviewView, self).get_mailer_kwargs()
        kwargs['order'] = Order.objects.order_by('?')[0]
        kwargs['summary_data'] = kwargs['order'].get_summary_data()
        return kwargs


class InvitePreviewView(PreviewView):
    mailer = InviteMailer
    kind = None

    def get_mailer_kwargs(self):
        kwargs = super(InvitePreviewView, self).get_mailer_kwargs()
        kwargs['invite'] = Invite.objects.filter(kind=self.kind).order_by('?')[0]
        kwargs['content'] = kwargs['invite'].get_content()
        kwargs['key'] = 'invite_{}'.format(self.kind)
        return kwargs
