from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models import Count, Sum
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.generic import (ListView, CreateView, UpdateView,
                                  TemplateView, DetailView, View)

from django_filters.views import FilterView

from floppyforms.__future__.models import modelform_factory
import requests
import stripe

from brambling.filters import AttendeeFilterSet, OrderFilterSet
from brambling.forms.organizer import (EventForm, ItemForm, ItemOptionFormSet,
                                       DiscountForm, DiscountChoiceForm)
from brambling.models import (Event, Item, Discount, Payment,
                              ItemOption, Attendee, Order,
                              BoughtItemDiscount, BoughtItem,
                              Refund, SubRefund)
from brambling.views.utils import (get_event_or_404,
                                   get_event_admin_nav, get_order,
                                   clear_expired_carts)


class EventCreateView(CreateView):
    model = Event
    template_name = 'brambling/event/create.html'
    context_object_name = 'event'
    form_class = EventForm

    def dispatch(self, request, *args, **kwargs):
        if request.method.lower() in self.http_method_names:
            if not request.user.is_authenticated():
                raise Http404
        return super(EventCreateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form, *args, **kwargs):
        "Force form owner to be the current user."
        form.instance.owner = self.request.user
        return super(EventCreateView, self).form_valid(form, *args, **kwargs)

    def get_initial(self):
        "Instantiate form with owner as current user."
        initial = {'owner': self.request.user}
        try:
            data = requests.get('http://api.hostip.info/get_json.php', timeout=.5).json()
        except requests.exceptions.Timeout:
            pass
        else:
            initial['country'] = data['country_code']
            if ', ' in data['city']:
                initial['city'], initial['state'] = data['city'].split(', ')

        return initial

    def get_form_class(self):
        return modelform_factory(self.model, form=self.form_class,
                                 exclude=('owner', 'editors', 'dates',
                                          'housing_dates'))


class EventSummaryView(TemplateView):
    template_name = 'brambling/event/summary.html'

    def get(self, request, *args, **kwargs):
        self.event = get_event_or_404(self.kwargs['slug'])
        if not self.event.editable_by(request.user):
            raise Http404
        clear_expired_carts(self.event)
        return super(EventSummaryView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(EventSummaryView, self).get_context_data(**kwargs)

        itemoptions = ItemOption.objects.filter(
            item__event=self.event
        ).select_related('item').annotate(Count('boughtitem'))

        gross_sales = 0
        itemoption_map = {}

        for itemoption in itemoptions:
            itemoption_map[itemoption.pk] = itemoption
            gross_sales += itemoption.price * itemoption.boughtitem__count

        discounts = list(Discount.objects.filter(
            event=self.event
        ).annotate(used_count=Count('boughtitemdiscount')))

        bought_item_discounts = BoughtItemDiscount.objects.filter(
            discount__in=discounts
        ).select_related('bought_item', 'discount')

        total_discounts = 0

        for discount in bought_item_discounts:
            if discount.bought_item.item_option_id in itemoption_map:
                discount.bought_item.item_option = itemoption_map[discount.bought_item.item_option_id]
            total_discounts += discount.savings()
        total_discounts = min(total_discounts, gross_sales)

        total_payments = Payment.objects.filter(order__event=self.event).aggregate(sum=Sum('amount'))['sum'] or 0

        context.update({
            'event': self.event,
            'order': get_order(self.event, self.request.user),
            'event_admin_nav': get_event_admin_nav(self.event, self.request),

            'attendee_count': Attendee.objects.filter(order__event=self.event).count(),
            'itemoptions': itemoptions,
            'discounts': discounts,

            'gross_sales': gross_sales,
            'total_discounts': total_discounts,
            'payments_received': total_payments,
            'payments_outstanding': gross_sales - total_discounts - total_payments
        })

        if self.event.collect_housing_data:
            context.update({
                'attendee_requesting_count': Attendee.objects.filter(order__event=self.event, housing_status=Attendee.NEED).count(),
                'attendee_arranged_count': Attendee.objects.filter(order__event=self.event, housing_status=Attendee.HAVE).count(),
                'attendee_home_count': Attendee.objects.filter(order__event=self.event, housing_status=Attendee.HOME).count(),
            })
        return context


class EventUpdateView(UpdateView):
    model = Event
    template_name = 'brambling/event/update.html'
    context_object_name = 'event'
    form_class = EventForm

    def get_object(self):
        obj = get_event_or_404(self.kwargs['slug'])
        user = self.request.user
        if not obj.editable_by(user):
            raise Http404
        return obj

    def get_success_url(self):
        return reverse('brambling_event_update',
                       kwargs={'slug': self.object.slug})

    def get_context_data(self, **kwargs):
        context = super(EventUpdateView, self).get_context_data(**kwargs)
        context.update({
            'cart': None,
            'event_admin_nav': get_event_admin_nav(self.object, self.request),
        })
        return context


class StripeConnectView(View):
    def get(self, request, *args, **kwargs):
        try:
            event = Event.objects.get(slug=request.GET.get('state'))
        except Event.DoesNotExist:
            raise Http404
        user = request.user
        if not event.editable_by(user):
            raise Http404
        if 'code' in request.GET:
            data = {
                'client_secret': settings.STRIPE_SECRET_KEY,
                'code': request.GET['code'],
                'grant_type': 'authorization_code',
            }
            r = requests.post("https://connect.stripe.com/oauth/token",
                              data=data)
            data = r.json()
            if 'access_token' in data:
                event.stripe_publishable_key = data['stripe_publishable_key']
                event.stripe_user_id = data['stripe_user_id']
                event.stripe_refresh_token = data['refresh_token']
                event.stripe_access_token = data['access_token']
                event.save()
                messages.success(request, 'Stripe account connected!')
            else:
                messages.error(request, 'Something went wrong. Please try again.')

        return HttpResponseRedirect(reverse('brambling_event_update',
                                            kwargs={'slug': event.slug}))


def item_form(request, *args, **kwargs):
    event = get_event_or_404(kwargs['event_slug'])
    if not event.editable_by(request.user):
        raise Http404
    if 'pk' in kwargs:
        item = get_object_or_404(Item, pk=kwargs['pk'])
    else:
        item = Item()
    if request.method == 'POST':
        form = ItemForm(event, request.POST, instance=item)
        formset = ItemOptionFormSet(event, request.POST, instance=item)
        # Always run both.
        form.is_valid()
        formset.is_valid()
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            url = reverse('brambling_item_list',
                          kwargs={'event_slug': event.slug})
            return HttpResponseRedirect(url)
    else:
        form = ItemForm(event, instance=item)
        formset = ItemOptionFormSet(event, instance=item)
    context = {
        'event': event,
        'item': item,
        'item_form': form,
        'itemoption_formset': formset,
        'cart': None,
        'event_admin_nav': get_event_admin_nav(event, request),
    }
    return render_to_response('brambling/event/item_form.html',
                              context,
                              context_instance=RequestContext(request))


class ItemListView(ListView):
    model = Item
    context_object_name = 'items'
    template_name = 'brambling/event/item_list.html'

    def get_queryset(self):
        self.event = get_event_or_404(self.kwargs['event_slug'])
        if not self.event.editable_by(self.request.user):
            raise Http404
        qs = super(ItemListView, self).get_queryset()
        return qs.filter(event=self.event
                         ).annotate(option_count=Count('options'))

    def get_context_data(self, **kwargs):
        context = super(ItemListView, self).get_context_data(**kwargs)
        context.update({
            'event': self.event,
            'cart': None,
            'event_admin_nav': get_event_admin_nav(self.event, self.request),
        })
        return context


def discount_form(request, *args, **kwargs):
    event = get_event_or_404(kwargs['event_slug'])
    if not event.editable_by(request.user):
        raise Http404
    if 'pk' in kwargs:
        discount = get_object_or_404(Discount, pk=kwargs['pk'])
    else:
        discount = None
    if request.method == 'POST':
        form = DiscountForm(event, request.POST, instance=discount)
        if form.is_valid():
            form.save()
            url = reverse('brambling_discount_list',
                          kwargs={'event_slug': event.slug})
            return HttpResponseRedirect(url)
    else:
        form = DiscountForm(event, instance=discount)
    context = {
        'event': event,
        'discount': form.instance,
        'discount_form': form,
        'cart': None,
        'event_admin_nav': get_event_admin_nav(event, request),
    }
    return render_to_response('brambling/event/discount_form.html',
                              context,
                              context_instance=RequestContext(request))


class DiscountListView(ListView):
    model = Discount
    context_object_name = 'discounts'
    template_name = 'brambling/event/discount_list.html'

    def get_queryset(self):
        self.event = get_event_or_404(self.kwargs['event_slug'])
        if not self.event.editable_by(self.request.user):
            raise Http404
        qs = super(DiscountListView, self).get_queryset()
        return qs.filter(event=self.event)

    def get_context_data(self, **kwargs):
        context = super(DiscountListView, self).get_context_data(**kwargs)
        context.update({
            'event': self.event,
            'cart': None,
            'event_admin_nav': get_event_admin_nav(self.event, self.request),
        })
        return context


class AttendeeFilterView(FilterView):
    filterset_class = AttendeeFilterSet
    template_name = 'brambling/event/attendees.html'
    context_object_name = 'attendees'

    def get_filterset(self, filterset_class):
        kwargs = self.get_filterset_kwargs(filterset_class)
        return filterset_class(self.event, **kwargs)

    def get_queryset(self):
        self.event = get_event_or_404(self.kwargs['event_slug'])
        if not self.event.editable_by(self.request.user):
            raise Http404
        qs = Attendee.objects.filter(
            order__event=self.event).distinct()
        return qs

    def get_context_data(self, **kwargs):
        context = super(AttendeeFilterView, self).get_context_data(**kwargs)
        context.update({
            'event': self.event,
            'event_admin_nav': get_event_admin_nav(self.event, self.request)
        })
        return context


class RefundView(View):
    form_class = None

    def get_object(self):
        self.event = get_event_or_404(self.kwargs['event_slug'])
        if not self.event.editable_by(self.request.user):
            raise Http404
        try:
            self.order = Order.objects.get(event=self.event,
                                           code=self.kwargs['code'])
        except Order.DoesNotExist:
            raise Http404
        return BoughtItem.objects.get(order=self.order,
                                      pk=self.kwargs['item_pk'])

    def get_context_data(self, **kwargs):
        context = super(AttendeeFilterView, self).get_context_data(**kwargs)
        context.update({
            'event': self.event,
            'event_admin_nav': get_event_admin_nav(self.event, self.request)
        })
        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        payments = self.object.subpayments.annotate(refunded=Sum('refunds__amount'))
        if not payments:
            self.object.delete()
        else:
            total_payments = sum((payment.amount for payment in payments))
            total_refunds = sum((payment.refunded or 0 for payment in payments))
            refundable = total_payments - total_refunds
            if refundable > 0:
                refund = Refund.objects.create(
                    order=self.order,
                    issuer=request.user,
                    bought_item=self.object,
                    amount=refundable,
                )

                stripe.api_key = settings.STRIPE_SECRET_KEY
                for payment in payments:
                    if payment.amount - (payment.refunded or 0) <= 0:
                        continue
                    stripe_charge = stripe.Charge.retrieve(payment.payment.remote_id)
                    amount = payment.amount - (payment.refunded or 0)
                    stripe_refund = stripe_charge.refund(
                        amount=amount * 100,
                    )
                    SubRefund.objects.create(
                        refund=refund,
                        subpayment=payment,
                        amount=amount,
                        method=payment.payment.method,
                        remote_id=stripe_refund.id
                    )
                self.object.status = BoughtItem.REFUNDED
                if self.object.attendee.event_pass == self.object:
                    self.object.attendee.delete()
                else:
                    self.object.attendee = None
                self.object.save()
        url = reverse('brambling_event_order_detail',
                      kwargs={'event_slug': self.event.slug,
                              'code': self.order.code})
        return HttpResponseRedirect(url)


class OrderFilterView(FilterView):
    filterset_class = OrderFilterSet
    template_name = 'brambling/event/orders.html'
    context_object_name = 'orders'

    def get_queryset(self):
        self.event = get_event_or_404(self.kwargs['event_slug'])
        if not self.event.editable_by(self.request.user):
            raise Http404
        qs = Order.objects.filter(event=self.event)
        return qs

    def get_context_data(self, **kwargs):
        context = super(OrderFilterView, self).get_context_data(**kwargs)
        context.update({
            'event': self.event,
            'event_admin_nav': get_event_admin_nav(self.event, self.request)
        })
        return context
