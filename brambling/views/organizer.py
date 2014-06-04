from django.core.urlresolvers import reverse
from django.db.models import Count, Sum
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.generic import ListView, CreateView, UpdateView, TemplateView

from django_filters.views import FilterView

from floppyforms.__future__.models import modelform_factory

from brambling.filters import PersonFilterSet
from brambling.forms.organizer import (EventForm, ItemForm, ItemOptionFormSet,
                                       DiscountForm)
from brambling.models import (Event, Item, Discount, EventPerson, Payment,
                              ItemOption, PersonItem, Person)
from brambling.views.utils import (get_event_or_404, get_event_nav,
                                   get_event_admin_nav)


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


class EventDashboardView(TemplateView):
    template_name = 'brambling/event/dashboard.html'

    def get(self, request, *args, **kwargs):
        self.event = get_event_or_404(self.kwargs['slug'])
        if not self.event.editable_by(request.user):
            raise Http404
        return super(EventDashboardView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(EventDashboardView, self).get_context_data(**kwargs)

        itemoptions = ItemOption.objects.filter(
            item__event=self.event
        ).select_related('item').annotate(Count('personitem'))

        gross_sales = 0
        itemoption_map = {}

        for itemoption in itemoptions:
            itemoption_map[itemoption.pk] = itemoption
            gross_sales += itemoption.price * itemoption.personitem__count

        discounts = Discount.objects.filter(
            event=self.event
        ).annotate(Count('persondiscount'))

        total_discounts = 0

        for discount in discounts:
            if discount.item_option_id in itemoption_map:
                itemoption = itemoption_map[discount.item_option_id]
                amount = (discount.amount
                          if discount.discount_type == Discount.FLAT
                          else discount.amount / 100 * itemoption.price)
                discount.used_count = PersonItem.objects.filter(
                    buyer__persondiscount__discount=discount,
                    item_option__discount=discount
                ).distinct().count()
                total_discounts += amount * discount.used_count
        total_discounts = min(total_discounts, gross_sales)

        total_payments = Payment.objects.filter(event=self.event).aggregate(sum=Sum('amount'))['sum'] or 0

        context.update({
            'event': self.event,
            'cart': self.request.user.get_cart(self.event),
            'event_nav': get_event_nav(self.event, self.request),
            'event_admin_nav': get_event_admin_nav(self.event, self.request),

            'attendee_count': EventPerson.objects.filter(event=self.event).count(),
            'itemoptions': itemoptions,
            'discounts': discounts,

            'gross_sales': gross_sales,
            'total_discounts': total_discounts,
            'payments_received': total_payments,
            'payments_outstanding': gross_sales - total_discounts - total_payments
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
            'cart': self.request.user.get_cart(self.object),
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
        formset = ItemOptionFormSet(request.POST, instance=item)
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
        formset = ItemOptionFormSet(instance=item)
    context = {
        'event': event,
        'item': item,
        'item_form': form,
        'itemoption_formset': formset,
        'cart': request.user.get_cart(event),
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
            'cart': self.request.user.get_cart(self.event),
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
        'cart': request.user.get_cart(event),
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
            'cart': self.request.user.get_cart(self.event),
            'event_nav': get_event_nav(self.event, self.request),
            'event_admin_nav': get_event_admin_nav(self.event, self.request),
        })
        return context


class PersonFilterView(FilterView):
    filterset_class = PersonFilterSet
    template_name = 'brambling/event/people.html'
    context_object_name = 'people'

    def get_filterset(self, filterset_class):
        kwargs = self.get_filterset_kwargs(filterset_class)
        return filterset_class(self.event, **kwargs)

    def get_queryset(self):
        self.event = get_event_or_404(self.kwargs['event_slug'])
        if not self.event.editable_by(self.request.user):
            raise Http404
        qs = Person.objects.filter(
            items_owned__item_option__item__event=self.event).distinct()
        return qs

    def get_context_data(self, **kwargs):
        context = super(PersonFilterView, self).get_context_data(**kwargs)
        context.update({
            'event': self.event,
            'event_nav': get_event_nav(self.event, self.request),
            'event_admin_nav': get_event_admin_nav(self.event, self.request)
        })
        return context
