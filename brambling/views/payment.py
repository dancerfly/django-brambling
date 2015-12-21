import json

from django.contrib import messages
from django.core.exceptions import SuspiciousOperation
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.http import is_safe_url
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from dwolla import oauth, accounts, webhooks

from brambling.models import Organization, Order, Transaction, Person, DwollaAccount
from brambling.utils.payment import (
    dwolla_prep,
    LIVE,
    dwolla_redirect_url,
)


class DwollaConnectView(View):
    def get_object(self):
        if self.request.GET.get('type') == 'person':
            model = Person
        elif self.request.GET.get('type') == 'order':
            model = Order
        elif self.request.GET.get('type') == 'organization':
            model = Organization
        else:
            raise Http404
        return get_object_or_404(model, pk=self.request.GET.get('id'))

    def get_success_url(self):
        if ('next_url' in self.request.GET and
                is_safe_url(url=self.request.GET['next_url'],
                            host=self.request.get_host())):
            return self.request.GET['next_url']

        if isinstance(self.object, Person):
            return reverse('brambling_user_profile')

        if isinstance(self.object, Order):
            return reverse('brambling_event_order_summary',
                           kwargs={'event_slug': self.object.event.slug,
                                   'organization_slug': self.object.event.organization.slug})

        if isinstance(self.object, Organization):
            return reverse('brambling_organization_update_payment',
                           kwargs={'organization_slug': self.object.slug})

        return '/'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if 'code' in request.GET:
            redirect_url = request.build_absolute_uri(reverse('brambling_dwolla_connect'))
            api_type = request.GET['api']
            dwolla_prep(api_type)
            redirect_url = dwolla_redirect_url(self.object, api_type, request, next_url=request.GET.get('next_url'))
            oauth_tokens = oauth.get(request.GET['code'],
                                     redirect=redirect_url)
            if 'access_token' in oauth_tokens:
                token = oauth_tokens['access_token']

                # Now get account info.
                account_info = accounts.full(token)

                try:
                    account = DwollaAccount.objects.get(api_type=api_type, user_id=account_info['Id'])
                except DwollaAccount.DoesNotExist:
                    account = DwollaAccount(api_type=api_type, user_id=account_info['Id'])

                account.set_tokens(oauth_tokens)

                account.save()
                if self.object.get_dwolla_account(api_type) != account:
                    if api_type == LIVE:
                        self.object.dwolla_user_new = account
                    else:
                        self.object.dwolla_test_user_new = account
                    self.object.save()
                messages.success(request, "Dwolla account connected!")
            elif 'error_description' in oauth_tokens:
                messages.error(request, oauth_tokens['error_description'])
            else:
                messages.error(request, "Unknown error during dwolla connection.")
        elif 'error_description' in request.GET:
            messages.error(request, request.GET['error_description'])
        else:
            messages.error(request, "Unknown error during dwolla connection.")

        return HttpResponseRedirect(self.get_success_url())


class DwollaWebhookView(View):
    @method_decorator(csrf_exempt)
    def post(self, request, *args, **kwargs):
        if request.META['CONTENT_TYPE'] != "application/json":
            raise Http404("Incorrect content type")

        try:
            data = json.loads(request.body)
        except ValueError:
            raise Http404("Webhook failed to decode request body")

        if data.get('Type') != 'Transaction' or data.get('Subtype') != 'Status':
            raise Http404("Unhandled webhook type: {} / {}".format(data.get('Type'), data.get('Subtype')))

        try:
            txn = Transaction.objects.get(remote_id=data['Transaction']['Id'])
        except Transaction.DoesNotExist:
            raise Http404("Transaction doesn't exist")
        except KeyError:
            raise Http404("Data doesn't contain transaction id")

        dwolla_prep(txn.api_type)
        if not webhooks.verify(request.META.get('HTTP_X_DWOLLA_SIGNATURE'), request.body):
            raise SuspiciousOperation("Transaction signature doesn't verify properly")

        txn.is_confirmed = True if data['Transaction']['Status'] == 'processed' else False
        txn.save()
        return HttpResponse('')
