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
import stripe

from brambling.models import (
    Order,
    Organization,
    Person,
    ProcessedStripeEvent,
    Transaction,
)
from brambling.payment.core import LIVE, TEST
from brambling.payment.stripe.core import stripe_prep


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
            api_type=api_type,
            stripe_event_id=stripe_event_id,
        )

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
