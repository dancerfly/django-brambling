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

from brambling.models import Organization, Order, Transaction, Event
from brambling.utils.payment import dwolla_prep, LIVE, dwolla_set_tokens


class DwollaConnectView(View):
    def get_object(self):
        raise NotImplementedError

    def get_success_url(self):
        raise NotImplementedError

    def get_redirect_url(self):
        raise NotImplementedError

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        redirect_url = self.object.get_dwolla_connect_url()
        api_type = request.GET['api']
        if 'code' in request.GET:
            qs = request.GET.copy()
            del qs['code']
            if qs:
                redirect_url += "?" + "&".join([k + "=" + v
                                                for k, v in qs.iteritems()])
            dwolla_prep(api_type)
            oauth_tokens = oauth.get(request.GET['code'],
                                     redirect=request.build_absolute_uri(redirect_url))
            if 'access_token' in oauth_tokens:
                token = oauth_tokens['access_token']

                # Now get account info.
                account_info = accounts.full(token)

                if api_type == LIVE:
                    self.object.dwolla_user_id = account_info['Id']
                else:
                    self.object.dwolla_test_user_id = account_info['Id']

                dwolla_set_tokens(self.object, api_type, oauth_tokens)

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


class OrganizationDwollaConnectView(DwollaConnectView):
    def get_object(self):
        return get_object_or_404(Organization, slug=self.kwargs['organization_slug'])

    def get_success_url(self):
        return reverse('brambling_organization_update_payment',
                       kwargs={'organization_slug': self.object.slug})


class UserDwollaConnectView(DwollaConnectView):
    def get_object(self):
        if not self.request.user.is_authenticated():
            raise Http404
        return self.request.user

    def get_success_url(self):
        request = self.request
        if ('next_url' in request.GET and
                is_safe_url(url=request.GET['next_url'],
                            host=request.get_host())):
            return request.GET['next_url']
        return reverse('brambling_user_profile')


class OrderDwollaConnectView(DwollaConnectView):
    def get_object(self):
        event = get_object_or_404(
            Event,
            slug=self.kwargs['event_slug'],
            organization__slug=self.kwargs['organization_slug']
        )

        try:
            return Order.objects.for_request(event, self.request, create=False)
        except Order.DoesNotExist:
            raise Http404

    def get_success_url(self):
        return reverse('brambling_event_order_summary',
                       kwargs={'event_slug': self.object.event.slug,
                               'organization_slug': self.object.event.organization.slug,
                               'code': self.object.code})


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
