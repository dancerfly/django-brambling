import logging
import operator
import pprint

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.utils import lookup_needs_distinct
from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import reverse
from django.db.models import Count, Sum, Q, Min, Max
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import (ListView, CreateView, UpdateView,
                                  TemplateView, DetailView, View)

from django_filters.views import FilterView

from floppyforms.__future__.models import modelform_factory
import requests

from brambling.filters import AttendeeFilterSet, OrderFilterSet
from brambling.forms.organizer import (EventForm, ItemForm, ItemOptionFormSet,
                                       DiscountForm, ItemImageFormSet,
                                       ManualPaymentForm, ManualDiscountForm,
                                       CustomFormForm, CustomFormFieldFormSet,
                                       OrderNotesForm)
from brambling.mail import send_order_receipt
from brambling.models import (Event, Item, Discount, Transaction,
                              ItemOption, Attendee, Order,
                              BoughtItemDiscount, BoughtItem,
                              Person, CustomForm, Organization)
from brambling.views.orders import OrderMixin, ApplyDiscountView
from brambling.views.utils import (get_event_or_404,
                                   get_event_admin_nav,
                                   clear_expired_carts,
                                   ajax_required)
from brambling.utils.model_tables import AttendeeTable, OrderTable
from brambling.utils.payment import (dwolla_can_connect, dwolla_organization_oauth_url,
                                     stripe_can_connect, stripe_organization_oauth_url,
                                     LIVE, TEST)


class OrganizationUpdateView(UpdateView):
    model = Organization
    template_name = 'brambling/organization/update.html'
    context_object_name = 'organization'

    def get_object(self):
        obj = get_object_or_404(Organization, slug=self.kwargs['organization_slug'])
        user = self.request.user
        if not obj.editable_by(user):
            raise Http404
        return obj

    def get_success_url(self):
        return reverse('brambling_organization_update',
                       kwargs={'slug': self.object.slug})

    def get_context_data(self, **kwargs):
        context = super(OrganizationUpdateView, self).get_context_data(**kwargs)

        if dwolla_can_connect(self.object, LIVE):
            context['dwolla_oauth_url'] = dwolla_organization_oauth_url(
                self.object, self.request, LIVE)

        if dwolla_can_connect(self.object, TEST):
            context['dwolla_test_oauth_url'] = dwolla_organization_oauth_url(
                self.object, self.request, TEST)

        if stripe_can_connect(self.object, LIVE):
            context['stripe_oauth_url'] = stripe_organization_oauth_url(
                self.object, self.request, LIVE)

        if stripe_can_connect(self.object, TEST):
            context['stripe_test_oauth_url'] = stripe_organization_oauth_url(
                self.object, self.request, TEST)

        return context


class OrganizationDetailView(DetailView):
    model = Organization
    template_name = 'brambling/organization/detail.html'
    slug_url_kwarg = 'organization_slug'

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except Http404:
            event = get_event_or_404(kwargs['organization_slug'])
            return HttpResponseRedirect(event.get_absolute_url())
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super(OrganizationDetailView, self).get_context_data(**kwargs)
        # TODO: This will probably cause timezone issues in some cases.
        today = timezone.now().date()
        upcoming_events = Event.objects.filter(
            organization=self.object,
            privacy=Event.PUBLIC,
            is_published=True,
        ).with_dates().filter(start_date__gte=today).order_by('start_date')

        admin_events = Event.objects.filter(
            Q(organization__owner=self.request.user) |
            Q(organization__editors=self.request.user) |
            Q(additional_editors=self.request.user),
            organization=self.object,
        ).with_dates().order_by('-last_modified')

        registered_events = list(Event.objects.filter(
            order__person=self.request.user,
            order__bought_items__status__in=(BoughtItem.BOUGHT, BoughtItem.RESERVED),
        ).with_dates().filter(start_date__gte=today).order_by('start_date'))

        context.update({
            'upcoming_events': upcoming_events,
            'admin_events': admin_events,
            'registered_events': registered_events,
        })
        return context


class EventCreateView(CreateView):
    model = Event
    template_name = 'brambling/event/organizer/create.html'
    context_object_name = 'event'
    form_class = EventForm

    def dispatch(self, request, *args, **kwargs):
        if request.method.lower() in self.http_method_names:
            if not request.user.is_authenticated() or not request.user.is_superuser:
                raise Http404
        return super(EventCreateView, self).dispatch(request, *args, **kwargs)

    def get_initial(self):
        "Instantiate form with owner as current user."
        initial = {
            'country': 'US',
        }
        try:
            data = requests.get('http://api.hostip.info/get_json.php', timeout=.5).json()
        except requests.exceptions.Timeout:
            pass
        else:
            if data['country_code'] == 'US' and ', ' in data['city']:
                initial['city'], initial['state'] = data['city'].split(', ')

        return initial

    def get_form_class(self):
        return modelform_factory(self.model, form=self.form_class)

    def get_form_kwargs(self):
        kwargs = super(EventCreateView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(EventCreateView, self).get_context_data(**kwargs)
        context['owner'] = self.request.user
        return context


class EventSummaryView(TemplateView):
    template_name = 'brambling/event/organizer/summary.html'

    def get(self, request, *args, **kwargs):
        self.event = get_event_or_404(self.kwargs['event_slug'])
        if not self.event.editable_by(request.user):
            raise Http404
        clear_expired_carts(self.event)
        return super(EventSummaryView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # For the summary, we only display completed order information.
        # We can show detailed information on a more detailed finances
        # page.
        context = super(EventSummaryView, self).get_context_data(**kwargs)

        itemoptions = ItemOption.objects.filter(
            item__event=self.event
        ).select_related('item')

        gross_sales = 0
        itemoption_map = {}

        for itemoption in itemoptions:
            itemoption_map[itemoption.pk] = itemoption
            itemoption.boughtitem__count = BoughtItem.objects.filter(
                item_option=itemoption,
                order__status__in=(Order.PENDING, Order.COMPLETED)
            ).count()
            gross_sales += itemoption.price * itemoption.boughtitem__count

        discounts = list(Discount.objects.filter(
            event=self.event
        ).annotate(used_count=Count('boughtitemdiscount')))

        confirmed_purchases = Transaction.objects.filter(
            transaction_type=Transaction.PURCHASE,
            event=self.event,
            is_confirmed=True,
        ).aggregate(sum=Sum('amount'))['sum'] or 0

        pending_purchases = Transaction.objects.filter(
            transaction_type=Transaction.PURCHASE,
            event=self.event,
            is_confirmed=False,
        ).aggregate(sum=Sum('amount'))['sum'] or 0

        refunds = Transaction.objects.filter(
            transaction_type=Transaction.REFUND,
            event=self.event,
        ).aggregate(sum=Sum('amount'))['sum'] or 0

        sums = Transaction.objects.filter(
            event=self.event,
        ).aggregate(
            amount=Sum('amount'),
            application_fee=Sum('application_fee'),
            processing_fee=Sum('processing_fee'),
        )

        fees = (sums['application_fee'] or 0) + (sums['processing_fee'] or 0)

        context.update({
            'event': self.event,
            'event_admin_nav': get_event_admin_nav(self.event, self.request),

            'attendee_count': Attendee.objects.filter(order__event=self.event).count(),
            'itemoptions': itemoptions,
            'discounts': discounts,

            'confirmed_purchases': confirmed_purchases,
            'pending_purchases': pending_purchases,

            'refunds': refunds,
            'fees': -1 * fees,

            'net_total': (sums['amount'] or 0) - fees,
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
        obj = get_event_or_404(self.kwargs['event_slug'])
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
            'owner': self.object.owner,
        })
        if dwolla_can_connect(self.object, self.object.api_type):
            context['dwolla_oauth_url'] = dwolla_event_oauth_url(
                self.object, self.request)
        if stripe_can_connect(self.object, self.object.api_type):
            context['stripe_oauth_url'] = stripe_event_oauth_url(
                self.object, self.request)
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
            if event.api_type == Event.LIVE:
                secret_key = settings.STRIPE_SECRET_KEY
            else:
                secret_key = settings.STRIPE_TEST_SECRET_KEY
            data = {
                'client_secret': secret_key,
                'code': request.GET['code'],
                'grant_type': 'authorization_code',
            }
            r = requests.post("https://connect.stripe.com/oauth/token",
                              data=data)
            data = r.json()
            if 'access_token' in data:
                if event.api_type == Event.LIVE:
                    event.stripe_publishable_key = data['stripe_publishable_key']
                    event.stripe_user_id = data['stripe_user_id']
                    event.stripe_refresh_token = data['refresh_token']
                    event.stripe_access_token = data['access_token']
                else:
                    event.stripe_test_publishable_key = data['stripe_publishable_key']
                    event.stripe_test_user_id = data['stripe_user_id']
                    event.stripe_test_refresh_token = data['refresh_token']
                    event.stripe_test_access_token = data['access_token']
                event.save()
                messages.success(request, 'Stripe account connected!')
            else:
                logger = logging.getLogger('brambling.stripe')
                logger.debug("Error connecting event {} ({}) to stripe. Data: {}".format(
                    event.pk, event.name, pprint.pformat(data)))
                messages.error(request, 'Something went wrong. Please try again.')

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


class PublishEventView(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            raise Http404
        try:
            event = Event.objects.get(slug=kwargs['event_slug'])
        except Event.DoesNotExist:
            raise Http404
        if not event.editable_by(request.user):
            raise Http404
        if not event.can_be_published():
            raise Http404
        if not event.is_published:
            event.is_published = True
            event.save()
        return HttpResponseRedirect(reverse('brambling_event_update', kwargs={'slug': event.slug}))


class UnpublishEventView(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            raise Http404
        try:
            event = Event.objects.get(slug=kwargs['event_slug'])
        except Event.DoesNotExist:
            raise Http404
        if event.is_frozen:
            raise Http404
        if not event.editable_by(request.user):
            raise Http404
        if event.is_published:
            event.is_published = False
            event.save()
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
        with timezone.override(event.timezone):
            # Clean as the event's timezone - datetimes
            # input correctly.
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
        with timezone.override(event.timezone):
            # Clean as the event's timezone - datetimes
            # input correctly.
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


def custom_form_form(request, *args, **kwargs):
    event = get_event_or_404(kwargs['event_slug'])
    if not event.editable_by(request.user):
        raise Http404
    if 'pk' in kwargs:
        custom_form = get_object_or_404(CustomForm, pk=kwargs['pk'])
    else:
        custom_form = CustomForm()
    if request.method == 'POST':
        form = CustomFormForm(event, request.POST, instance=custom_form)
        formset = CustomFormFieldFormSet(data=request.POST, files=request.FILES, instance=custom_form, prefix='fields')
        form.is_valid()
        formset.is_valid()
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            url = reverse('brambling_form_list',
                          kwargs={'event_slug': event.slug})
            return HttpResponseRedirect(url)
    else:
        form = CustomFormForm(event, instance=custom_form)
        formset = CustomFormFieldFormSet(instance=custom_form, prefix='fields')
    context = {
        'event': event,
        'custom_form': form.instance,
        'form': form,
        'formset': formset,
        'event_admin_nav': get_event_admin_nav(event, request),
    }
    return render_to_response('brambling/event/organizer/custom_form_form.html',
                              context,
                              context_instance=RequestContext(request))


class CustomFormListView(ListView):
    model = CustomForm
    context_object_name = 'custom_forms'
    template_name = 'brambling/event/organizer/custom_form_list.html'

    def get_queryset(self):
        self.event = get_event_or_404(self.kwargs['event_slug'])
        if not self.event.editable_by(self.request.user):
            raise Http404
        qs = super(CustomFormListView, self).get_queryset()
        return qs.filter(event=self.event).order_by('form_type', 'index')

    def get_context_data(self, **kwargs):
        context = super(CustomFormListView, self).get_context_data(**kwargs)
        context.update({
            'event': self.event,
            'event_admin_nav': get_event_admin_nav(self.event, self.request),
        })
        return context


class ModelTableView(FilterView):
    search_fields = None
    model_table = None
    form_prefix = 'column'

    def get_table_kwargs(self, queryset):
        kwargs = {
            'queryset': queryset,
            'form_prefix': self.form_prefix,
        }
        if self.request.GET:
            kwargs['data'] = self.request.GET
        return kwargs

    def get_table(self, queryset):
        if not self.model_table:
            raise ValueError("model_table cannot be None")
        return self.model_table(**self.get_table_kwargs(queryset))

    def get_context_data(self, **kwargs):
        context = super(ModelTableView, self).get_context_data(**kwargs)
        context['table'] = self.get_table(self.object_list)
        return context

    def get_queryset(self):
        queryset = super(ModelTableView, self).get_queryset()

        # Originally from django.contrib.admin.options
        def construct_search(field_name):
            if field_name.startswith('^'):
                return "%s__istartswith" % field_name[1:]
            elif field_name.startswith('='):
                return "%s__iexact" % field_name[1:]
            elif field_name.startswith('@'):
                return "%s__search" % field_name[1:]
            else:
                return "%s__icontains" % field_name

        use_distinct = False
        search_fields = self.search_fields
        search_term = self.request.GET.get('search', '')
        opts = self.model._meta
        if search_fields and search_term:
            orm_lookups = [construct_search(str(search_field))
                           for search_field in search_fields]
            for bit in search_term.split():
                or_queries = [Q(**{orm_lookup: bit})
                              for orm_lookup in orm_lookups]
                queryset = queryset.filter(reduce(operator.or_, or_queries))
            if not use_distinct:
                for search_spec in orm_lookups:
                    if lookup_needs_distinct(opts, search_spec):
                        use_distinct = True
                        break

        if use_distinct:
            queryset = queryset.distinct()
        return queryset

    def render_to_response(self, context, *args, **kwargs):
        "Return a response in the requested format."

        format_ = self.request.GET.get('format', default='html')

        if format_ == 'csv':
            return context['table'].render_csv_response()
        else:
            # Default to the template.
            return super(ModelTableView, self).render_to_response(context, *args, **kwargs)


class AttendeeFilterView(ModelTableView):
    filterset_class = AttendeeFilterSet
    template_name = 'brambling/event/organizer/attendees.html'
    context_object_name = 'attendees'
    search_fields = ('given_name', 'middle_name', 'surname', 'order__code',
                     'email', 'order__email', 'order__person__email')
    model = Attendee
    model_table = AttendeeTable

    def get_queryset(self):
        self.event = get_event_or_404(self.kwargs['event_slug'])
        if not self.event.editable_by(self.request.user):
            raise Http404
        qs = super(AttendeeFilterView, self).get_queryset()
        return qs.filter(order__event=self.event).distinct()

    def get_filterset_kwargs(self, filterset_class):
        kwargs = super(AttendeeFilterView, self).get_filterset_kwargs(filterset_class)
        kwargs['event'] = self.event
        return kwargs

    def get_table_kwargs(self, queryset):
        kwargs = super(AttendeeFilterView, self).get_table_kwargs(queryset)
        kwargs['event'] = self.event
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(AttendeeFilterView, self).get_context_data(**kwargs)
        context.update({
            'event': self.event,
            'event_admin_nav': get_event_admin_nav(self.event, self.request)
        })
        return context


class RefundView(View):
    def get_object(self):
        self.event = get_event_or_404(self.kwargs['event_slug'])
        if not self.event.editable_by(self.request.user):
            raise Http404
        try:
            return Transaction.objects.get(
                event=self.event,
                order__code=self.kwargs['code'],
                pk=self.kwargs['pk']
            )
        except Transaction.DoesNotExist:
            raise Http404

    def post(self, request, *args, **kwargs):
        txn = self.get_object()
        try:
            txn.refund(issuer=request.user,
                       dwolla_pin=request.POST.get('dwolla_pin'))
        except Exception as e:
            messages.error(request, e.message)

        url = reverse('brambling_event_order_detail',
                      kwargs={'event_slug': self.event.slug,
                              'code': self.kwargs['code']})
        return HttpResponseRedirect(url)


class OrderFilterView(ModelTableView):
    filterset_class = OrderFilterSet
    template_name = 'brambling/event/organizer/orders.html'
    context_object_name = 'orders'
    search_fields = ('code', 'email', 'person__email')
    model = Order
    model_table = OrderTable

    def get_queryset(self):
        self.event = get_event_or_404(self.kwargs['event_slug'])
        if not self.event.editable_by(self.request.user):
            raise Http404
        qs = super(OrderFilterView, self).get_queryset()
        return qs.filter(event=self.event)

    def get_table_kwargs(self, queryset):
        kwargs = super(OrderFilterView, self).get_table_kwargs(queryset)
        kwargs['event'] = self.event
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(OrderFilterView, self).get_context_data(**kwargs)
        context.update({
            'event': self.event,
            'event_admin_nav': get_event_admin_nav(self.event, self.request)
        })
        return context


class OrganizerApplyDiscountView(ApplyDiscountView):
    def get_order(self):
        return Order.objects.get(event=self.event, code=self.kwargs['code'])


class RemoveDiscountView(OrderMixin, View):
    @method_decorator(ajax_required)
    def post(self, request, *args, **kwargs):
        if not self.is_admin_request:
            raise Http404
        try:
            boughtitemdiscount = BoughtItemDiscount.objects.get(
                bought_item__order=self.order,
                pk=kwargs['discount_pk']
            )
        except BoughtItemDiscount.DoesNotExist:
            pass
        else:
            boughtitemdiscount.delete()
        return JsonResponse({'success': True})

    def get_workflow(self):
        return None

    def get_order(self):
        return Order.objects.get(event=self.event, code=self.kwargs['code'])


class OrderDetailView(DetailView):
    template_name = 'brambling/event/organizer/order_detail.html'

    def get_object(self):
        return self.order

    def get_forms(self):
        self.event = get_event_or_404(self.kwargs['event_slug'])
        if not self.event.editable_by(self.request.user):
            raise Http404
        self.order = get_object_or_404(Order, event=self.event,
                                       code=self.kwargs['code'])
        self.payment_form = ManualPaymentForm(order=self.order, user=self.request.user)
        self.discount_form = ManualDiscountForm(order=self.order)
        self.notes_form = OrderNotesForm(instance=self.order)
        if self.request.method == 'POST':
            if 'is_payment_form' in self.request.POST:
                self.payment_form = ManualPaymentForm(order=self.order,
                                                      user=self.request.user,
                                                      data=self.request.POST)
            elif 'is_discount_form' in self.request.POST:
                self.discount_form = ManualDiscountForm(order=self.order,
                                                        data=self.request.POST)
            elif 'is_notes_form' in self.request.POST:
                self.notes_form = OrderNotesForm(instance=self.order,
                                                 data=self.request.POST)
        return self.payment_form, self.discount_form, self.notes_form

    def get_context_data(self, **kwargs):
        context = super(OrderDetailView, self).get_context_data(**kwargs)
        if self.payment_form.is_bound:
            active = 'payment'
        elif self.discount_form.is_bound:
            active = 'discount'
        elif self.notes_form.is_bound or self.request.GET.get('active') == 'notes':
            active = 'notes'
        else:
            active = 'summary'
        context.update({
            'payment_form': self.payment_form,
            'discount_form': self.discount_form,
            'notes_form': self.notes_form,
            'order': self.order,
            'event': self.event,
            'event_admin_nav': get_event_admin_nav(self.event, self.request),
            'active': active,
        })
        context.update(self.order.get_summary_data())
        return context

    def get(self, request, *args, **kwargs):
        self.get_forms()
        return super(OrderDetailView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        for form in self.get_forms():
            if form.is_bound and form.is_valid():
                form.save()
                path = request.path
                if 'active' in request.GET:
                    path += '?active=' + request.GET['active']
                return HttpResponseRedirect(path)
        return super(OrderDetailView, self).get(request, *args, **kwargs)


class TogglePaymentConfirmationView(View):
    def get_object(self):
        self.event = get_event_or_404(self.kwargs['event_slug'])
        if not self.event.editable_by(self.request.user):
            raise Http404
        try:
            self.order = Order.objects.get(event=self.event,
                                           code=self.kwargs['code'])
            return Transaction.objects.get(transaction_type=Transaction.PURCHASE,
                                           order=self.order,
                                           pk=self.kwargs['payment_pk'])
        except (Order.DoesNotExist, Transaction.DoesNotExist):
            raise Http404

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.is_confirmed = not self.object.is_confirmed
        self.object.save()
        all_confirmed = not self.order.transactions.filter(is_confirmed=False).exists()
        self.order.status = Order.COMPLETED if all_confirmed else Order.PENDING
        self.order.save()
        return JsonResponse({'success': True, 'is_confirmed': self.object.is_confirmed})


class SendReceiptView(View):
    def get(self, request, *args, **kwargs):
        event = get_event_or_404(self.kwargs['event_slug'])
        if not event.editable_by(self.request.user):
            raise Http404
        try:
            order = Order.objects.get(event=event,
                                      code=self.kwargs['code'])
        except Order.DoesNotExist:
            raise Http404
        send_order_receipt(order, order.get_summary_data(),
                           get_current_site(request),
                           event=event, secure=request.is_secure())
        messages.success(request, 'Receipt sent to {}!'.format(order.person.email if order.person else order.email))
        return HttpResponseRedirect(reverse('brambling_event_order_detail', kwargs={'event_slug': event.slug, 'code': order.code}))


class FinancesView(ListView):
    model = Transaction
    context_object_name = 'transactions'
    template_name = 'brambling/event/organizer/finances.html'

    def get_queryset(self):
        self.event = get_event_or_404(self.kwargs['event_slug'])
        if not self.event.editable_by(self.request.user):
            raise Http404
        return super(FinancesView, self).get_queryset().filter(
            event=self.event,
            api_type=self.event.api_type,
        ).select_related('created_by', 'order').order_by('-timestamp')

    def get_context_data(self, **kwargs):
        context = super(FinancesView, self).get_context_data(**kwargs)
        context.update({
            'event': self.event,
            'event_admin_nav': get_event_admin_nav(self.event, self.request),
        })
        return context
