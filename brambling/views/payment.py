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
import stripe

from brambling.models import (
    DwollaAccount,
    Order,
    Organization,
    Person,
    ProcessedStripeEvent,
    Transaction,
)
from brambling.payment.core import LIVE, TEST
from brambling.payment.dwolla.auth import dwolla_redirect_url
from brambling.payment.dwolla.core import dwolla_prep
from brambling.payment.stripe.core import stripe_prep


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
            return reverse('brambling_user_billing')

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
                        self.object.dwolla_account = account
                    else:
                        self.object.dwolla_test_account = account
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
    def dispatch(self, *args, **kwargs):
        return super(DwollaWebhookView, self).dispatch(*args, **kwargs)

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


class StripeWebhookView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(StripeWebhookView, self).dispatch(*args, **kwargs)

    def post(self, request):
        if request.META['CONTENT_TYPE'] != 'application/json':
            raise Http404('Incorrect content type')

        try:
            event_data = json.loads(request.body)
        except ValueError:
            raise Http404('Webhook failed to decode request body')

        stripe_event_id = event_data.get('id')
        if not stripe_event_id:
            raise Http404('Event does not have an id')

        if event_data.get('livemode', False):
            stripe_prep(LIVE)
        else:
            stripe_prep(TEST)

        try:
            event = stripe.Event.retrieve(stripe_event_id)
        except stripe.error.InvalidRequestError:
            raise Http404('Event not found on stripe')

        if event.type != 'charge.refunded':
            return HttpResponse(status=200)

        if event.livemode:
            api_type = ProcessedStripeEvent.LIVE
        else:
            api_type = ProcessedStripeEvent.TEST

        _, new_event = ProcessedStripeEvent.objects.get_or_create(
            api_type=api_type, stripe_event_id=stripe_event_id)

        if not new_event:
            return HttpResponse(status=200)

        try:
            charge_id = event.data.object.id
            txn = Transaction.objects.get(
                remote_id=charge_id,
                api_type=api_type,
            )
        except Transaction.DoesNotExist:
            return HttpResponse(status=200)
        except AttributeError:
            raise Http404('Charge id not found')

        event = txn.event
        if event.api_type == LIVE:
            access_token = event.organization.stripe_access_token
        else:
            access_token = event.organization.stripe_test_access_token
        stripe.api_key = access_token

        try:
            charge = stripe.Charge.retrieve(
                charge_id,
                expand=[
                    'balance_transaction',
                    'application_fee',
                    'refunds.balance_transaction',
                ],
            )
        except stripe.error.InvalidRequestError:
            raise Http404('Charge not found on stripe')

        for refund in charge.refunds:
            if Transaction.objects.filter(
                transaction_type=Transaction.REFUND,
                method=Transaction.STRIPE,
                remote_id=refund.id,
                related_transaction=txn,
            ).exists():
                continue
            application_fee_refund = charge.application_fee.refunds.data[0]
            refund_group = {
                'refund': refund,
                'application_fee_refund': application_fee_refund,
            }

            refund_kwargs = {
                'order': txn.order,
                'related_transaction': txn,
                'api_type': txn.api_type,
                'event': txn.event,
            }
            Transaction.from_stripe_refund(refund_group, **refund_kwargs)

        return HttpResponse(status=200)
