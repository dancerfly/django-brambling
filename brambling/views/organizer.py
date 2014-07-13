from django.core.urlresolvers import reverse
from django.db.models import Count, Sum
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.generic import ListView, CreateView, UpdateView, TemplateView

from django_filters.views import FilterView

from floppyforms.__future__.models import modelform_factory

from brambling.filters import AttendeeFilterSet
from brambling.forms.organizer import (EventForm, ItemForm, ItemOptionFormSet,
                                       DiscountForm)
from brambling.models import (Event, Item, Discount, Payment,
                              ItemOption, Attendee, OrderDiscount,
                              BoughtItemDiscount)
from brambling.views.utils import (get_event_or_404, get_event_nav,
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
        return {'owner': self.request.user}

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
            'event_nav': get_event_nav(self.event, self.request),
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

    def get_context_data(self, **kwargs):
        context = super(EventUpdateView, self).get_context_data(**kwargs)
        context.update({
            'cart': None,
            'event_nav': get_event_nav(self.object, self.request),
            'event_admin_nav': get_event_admin_nav(self.object, self.request),
        })
        return context


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
        'event_nav': get_event_nav(event, request),
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
            'event_nav': get_event_nav(self.event, self.request),
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
        'event_nav': get_event_nav(event, request),
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
            'event_nav': get_event_nav(self.event, self.request),
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
            'event_nav': get_event_nav(self.event, self.request),
            'event_admin_nav': get_event_admin_nav(self.event, self.request)
        })
        return context
