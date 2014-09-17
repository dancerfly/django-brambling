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
                                       DiscountForm, ItemImageFormSet,
                                       ManualPaymentForm, ManualDiscountForm)
from brambling.models import (Event, Item, Discount, Payment,
                              ItemOption, Attendee, Order,
                              BoughtItemDiscount, BoughtItem,
                              Refund, SubRefund, Person)
from brambling.views.utils import (get_event_or_404, get_dwolla,
                                   get_event_admin_nav, get_order,
                                   clear_expired_carts)
from brambling.utils.model_tables import AttendeeTable, OrderTable


class EventCreateView(CreateView):
    model = Event
    template_name = 'brambling/event/organizer/create.html'
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

    def get_form_kwargs(self):
        kwargs = super(EventCreateView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class EventSummaryView(TemplateView):
    template_name = 'brambling/event/organizer/summary.html'

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
    template_name = 'brambling/event/organizer/update.html'
    context_object_name = 'event'
    form_class = EventForm

    def get_object(self):
        obj = get_event_or_404(self.kwargs['slug'])
        user = self.request.user
        if not obj.editable_by(user):
            raise Http404
        return obj

    def get_form_kwargs(self):
        kwargs = super(EventUpdateView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_success_url(self):
        return reverse('brambling_event_update',
                       kwargs={'slug': self.object.slug})

    def get_context_data(self, **kwargs):
        context = super(EventUpdateView, self).get_context_data(**kwargs)
        context.update({
            'cart': None,
            'event_admin_nav': get_event_admin_nav(self.object, self.request),
        })
        if getattr(settings, 'DWOLLA_APPLICATION_KEY', None) and not self.object.uses_dwolla():
            dwolla = get_dwolla()
            client = dwolla.DwollaClientApp(settings.DWOLLA_APPLICATION_KEY,
                                            settings.DWOLLA_APPLICATION_SECRET)
            redirect_url = reverse('brambling_dwolla_connect') + "?state=" + self.object.slug
            context['dwolla_oauth_url'] = client.init_oauth_url(self.request.build_absolute_uri(redirect_url),
                                                                "Send|AccountInfoFull|Transactions")
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


class DwollaConnectView(View):
    def get(self, request, *args, **kwargs):
        try:
            event = Event.objects.get(slug=request.GET.get('state'))
        except Event.DoesNotExist:
            raise Http404
        dwolla = get_dwolla()
        client = dwolla.DwollaClientApp(settings.DWOLLA_APPLICATION_KEY,
                                        settings.DWOLLA_APPLICATION_SECRET)
        redirect_url = reverse('brambling_dwolla_connect') + "?state=" + request.GET['state']
        token = client.get_oauth_token(request.GET['code'],
                                       redirect_uri=request.build_absolute_uri(redirect_url))

        event.dwolla_access_token = token

        # Now get account info.
        dwolla_user = dwolla.DwollaUser(token)
        event.dwolla_user_id = dwolla_user.get_account_info()['Id']
        event.save()

        return HttpResponseRedirect(reverse('brambling_event_update',
                                            kwargs={'slug': event.slug}))


class RemoveEditorView(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            raise Http404
        try:
            event = Event.objects.get(slug=kwargs['event_slug'])
        except Event.DoesNotExist:
            raise Http404
        if not event.owner_id == request.user.pk:
            raise Http404
        try:
            person = Person.objects.get(pk=kwargs['pk'])
        except Person.DoesNotExist:
            pass
        else:
            event.editors.remove(person)
        messages.success(request, 'Removed editor successfully.')
        return HttpResponseRedirect(reverse('brambling_event_update', kwargs={'slug': event.slug}))


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
        image_formset = ItemImageFormSet(data=request.POST, files=request.FILES, instance=item, prefix='image')
        formset = ItemOptionFormSet(event, request.POST, instance=item, prefix='option')
        # Always run all.
        form.is_valid()
        image_formset.is_valid()
        formset.is_valid()
        if form.is_valid() and image_formset.is_valid() and formset.is_valid():
            form.save()
            image_formset.save()
            formset.save()
            url = reverse('brambling_item_list',
                          kwargs={'event_slug': event.slug})
            return HttpResponseRedirect(url)
    else:
        form = ItemForm(event, instance=item)
        image_formset = ItemImageFormSet(instance=item, prefix='image')
        formset = ItemOptionFormSet(event, instance=item, prefix='option')
    context = {
        'event': event,
        'item': item,
        'item_form': form,
        'itemimage_formset': image_formset,
        'itemoption_formset': formset,
        'cart': None,
        'event_admin_nav': get_event_admin_nav(event, request),
    }
    return render_to_response('brambling/event/organizer/item_form.html',
                              context,
                              context_instance=RequestContext(request))


class ItemListView(ListView):
    model = Item
    context_object_name = 'items'
    template_name = 'brambling/event/organizer/item_list.html'

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
    return render_to_response('brambling/event/organizer/discount_form.html',
                              context,
                              context_instance=RequestContext(request))


class DiscountListView(ListView):
    model = Discount
    context_object_name = 'discounts'
    template_name = 'brambling/event/organizer/discount_list.html'

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
    template_name = 'brambling/event/organizer/attendees.html'
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

    def get_table(self, queryset):
        if self.request.GET:
            return AttendeeTable(self.event, queryset, data=self.request.GET, form_prefix="column")
        else:
            return AttendeeTable(self.event, queryset, form_prefix="column")

    def get_context_data(self, **kwargs):
        context = super(AttendeeFilterView, self).get_context_data(**kwargs)
        context.update({
            'table': self.get_table(self.object_list),
            'event': self.event,
            'event_admin_nav': get_event_admin_nav(self.event, self.request)
        })
        return context

    def render_to_response(self, context, *args, **kwargs):
        "Return a response in the requested format."

        format_ = self.request.GET.get('format', default='html')

        if format_ == 'csv':
            table = self.get_table(self.get_queryset())
            return table.render_csv_response()
        else:
            # Default to the template.
            return super(AttendeeFilterView, self).render_to_response(context, *args, **kwargs)


class RefundView(View):
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

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        subpayments = self.object.subpayments.annotate(refunded=Sum('refunds__amount'))
        if not subpayments:
            self.object.delete()
        else:
            total_payments = sum((subpayment.amount for subpayment in subpayments))
            total_refunds = sum((subpayment.refunded or 0 for subpayment in subpayments))
            refundable = total_payments - total_refunds
            if refundable > 0:
                refund = Refund.objects.create(
                    order=self.order,
                    issuer=request.user,
                    bought_item=self.object,
                    amount=refundable,
                )

                stripe.api_key = settings.STRIPE_SECRET_KEY
                dwolla = get_dwolla()
                try:
                    for subpayment in subpayments:
                        amount = subpayment.amount - (subpayment.refunded or 0)
                        if amount <= 0:
                            continue
                        if subpayment.payment.method == Payment.STRIPE:
                            stripe_charge = stripe.Charge.retrieve(subpayment.payment.remote_id)
                            stripe_refund = stripe_charge.refund(
                                amount=amount * 100,
                            )
                            remote_id = stripe_refund.id
                        elif subpayment.payment.method == Payment.DWOLLA:
                            dwolla_user = dwolla.DwollaUser(self.event.dwolla_access_token)
                            dwolla_refund = dwolla_user.refund(int(subpayment.payment.remote_id),
                                                               "%.2f" % amount,
                                                               int(request.POST.get('dwolla_pin')))
                            remote_id = dwolla_refund['TransactionId']

                        SubRefund.objects.create(
                            refund=refund,
                            subpayment=subpayment,
                            amount=amount,
                            method=subpayment.payment.method,
                            remote_id=remote_id
                        )
                except dwolla.DwollaAPIError, e:
                    refund.delete()
                    messages.error(request, e.message)
                else:
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
    template_name = 'brambling/event/organizer/orders.html'
    context_object_name = 'orders'

    def get_queryset(self):
        self.event = get_event_or_404(self.kwargs['event_slug'])
        if not self.event.editable_by(self.request.user):
            raise Http404
        qs = Order.objects.filter(event=self.event)
        return qs

    def get_table(self, queryset):
        if self.request.GET:
            return OrderTable(self.event, queryset, data=self.request.GET, form_prefix="column")
        else:
            return OrderTable(self.event, queryset, form_prefix="column")

    def get_context_data(self, **kwargs):
        context = super(OrderFilterView, self).get_context_data(**kwargs)
        context.update({
            'table': self.get_table(self.object_list),
            'event': self.event,
            'event_admin_nav': get_event_admin_nav(self.event, self.request)
        })
        return context


class OrderDetailView(DetailView):
    template_name = 'brambling/event/organizer/order_detail.html'

    def get_object(self):
        return self.order

    def get_forms(self):
        self.event = get_event_or_404(self.kwargs['event_slug'])
        if not self.event.editable_by(self.request.user):
            raise Http404
        self.order = get_order(self.event, code=self.kwargs['code'])
        self.payment_form = ManualPaymentForm(order=self.order)
        self.discount_form = ManualDiscountForm(order=self.order)
        if self.request.method == 'POST':
            if 'is_payment_form' in self.request.POST:
                self.payment_form = ManualPaymentForm(order=self.order,
                                                      data=self.request.POST)
            elif 'is_discount_form' in self.request.POST:
                self.discount_form = ManualDiscountForm(order=self.order,
                                                        data=self.request.POST)

    def get_context_data(self, **kwargs):
        context = super(OrderDetailView, self).get_context_data(**kwargs)
        context.update({
            'payment_form': self.payment_form,
            'discount_form': self.discount_form,
            'order': self.order,
            'event': self.event,
            'event_admin_nav': get_event_admin_nav(self.event, self.request),
        })
        context.update(self.order.get_summary_data())
        return context

    def get(self, request, *args, **kwargs):
        self.get_forms()
        return super(OrderDetailView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.get_forms()
        if self.payment_form.is_bound and self.payment_form.is_valid():
            self.payment_form.save()
            return HttpResponseRedirect(request.path)
        if self.discount_form.is_bound and self.discount_form.is_valid():
            self.discount_form.save()
            return HttpResponseRedirect(request.path)
        return super(OrderDetailView, self).get(request, *args, **kwargs)
