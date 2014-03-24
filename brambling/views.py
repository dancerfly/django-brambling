from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.forms.models import modelform_factory
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.generic import (ListView, DetailView, CreateView, UpdateView,
                                  TemplateView)

from brambling.forms import (EventForm, PersonForm, HouseForm, ItemForm,
                             ItemOptionFormSet, formfield_callback,
                             ItemDiscountFormSet, DiscountForm, SignUpForm)
from brambling.models import (Event, Person, House, Item,
                              Discount, ItemDiscount)


def home(request):
    if request.user.is_authenticated():
        return Dashboard.as_view()(request)
    else:
        return EventListView.as_view()(request)


class Dashboard(TemplateView):
    template_name = "brambling/dashboard.html"

    def get_context_data(self):
        current_user = self.request.user
        events = Event.objects.filter(privacy=Event.PUBLIC)
        query = Q(owner=current_user) | Q(editors=current_user)
        your_events = Event.objects.filter(query)
        return {'events': events, 'your_events': your_events}

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(Dashboard, self).dispatch(*args, **kwargs)


class EventListView(ListView):
    model = Event
    template_name = 'brambling/event_list.html'
    context_object_name = 'events'

    def get_queryset(self):
        qs = super(EventListView, self).get_queryset()
        return qs.filter(privacy=Event.PUBLIC)


class EventDetailView(DetailView):
    model = Event
    template_name = 'brambling/event_detail.html'
    context_object_name = 'event'

    def get_object(self):
        obj = super(EventDetailView, self).get_object()
        if obj.privacy == Event.PRIVATE:
            user = self.request.user
            if not obj.can_edit(user):
                raise Http404
        return obj

    def get_queryset(self):
        queryset = super(EventDetailView, self).get_queryset()
        return queryset.prefetch_related('editors')


class EventCreateView(CreateView):
    model = Event
    template_name = 'brambling/event_form.html'
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
                                 exclude=('owner', 'editors'),
                                 formfield_callback=formfield_callback)


class EventUpdateView(UpdateView):
    model = Event
    template_name = 'brambling/event_form.html'
    context_object_name = 'event'
    form_class = EventForm

    def get_object(self):
        obj = super(EventUpdateView, self).get_object()
        user = self.request.user
        if not obj.can_edit(user):
            raise Http404
        return obj


class PersonView(UpdateView):
    model = Person
    form_class = PersonForm

    def get_object(self):
        if self.request.user.is_authenticated():
            return self.request.user
        raise Http404


class HouseView(UpdateView):
    model = House
    form_class = HouseForm

    def get_object(self):
        if not self.request.user.is_authenticated():
            raise Http404
        return (House.objects.filter(residents=self.request.user).first() or
                House())

    def get_form_kwargs(self):
        kwargs = super(HouseView, self).get_form_kwargs()
        kwargs['person'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('brambling_house')


def item_form(request, *args, **kwargs):
    event = get_object_or_404(Event, slug=kwargs['event_slug'])
    if not event.can_edit(request.user):
        raise Http404
    if 'pk' in kwargs:
        item = get_object_or_404(Item, pk=kwargs['pk'])
    else:
        item = Item()
    if request.method == 'POST':
        form = ItemForm(event, request.POST, instance=item)
        formset = ItemOptionFormSet(request.POST, instance=item)
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
    }
    return render_to_response('brambling/item_form.html',
                              context,
                              context_instance=RequestContext(request))


class ItemListView(ListView):
    model = Item
    context_object_name = 'items'

    def get_queryset(self):
        self.event = get_object_or_404(Event, slug=self.kwargs['event_slug'])
        if not self.event.can_edit(self.request.user):
            raise Http404
        qs = super(ItemListView, self).get_queryset()
        return qs.filter(event=self.event)

    def get_context_data(self, **kwargs):
        context = super(ItemListView, self).get_context_data(**kwargs)
        context['event'] = self.event
        return context


def discount_form(request, *args, **kwargs):
    event = get_object_or_404(Event, slug=kwargs['event_slug'])
    if not event.can_edit(request.user):
        raise Http404
    if 'pk' in kwargs:
        discount = get_object_or_404(Discount, pk=kwargs['pk'])
    else:
        discount = Discount()
    if request.method == 'POST':
        form = DiscountForm(event, request.POST, instance=discount)
        formset = ItemDiscountFormSet(request.POST, instance=discount)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            url = reverse('brambling_discount_list',
                          kwargs={'event_slug': event.slug})
            return HttpResponseRedirect(url)
    else:
        form = DiscountForm(event, instance=discount)
        formset = ItemDiscountFormSet(instance=discount)
    context = {
        'event': event,
        'discount': discount,
        'discount_form': form,
        'itemdiscount_formset': formset,
    }
    return render_to_response('brambling/discount_form.html',
                              context,
                              context_instance=RequestContext(request))


class DiscountListView(ListView):
    model = Discount
    context_object_name = 'discounts'
    template_name = 'brambling/discount_list.html'

    def get_queryset(self):
        self.event = get_object_or_404(Event, slug=self.kwargs['event_slug'])
        if not self.event.can_edit(self.request.user):
            raise Http404
        qs = super(DiscountListView, self).get_queryset()
        return qs.filter(event=self.event)

    def get_context_data(self, **kwargs):
        context = super(DiscountListView, self).get_context_data(**kwargs)
        context['event'] = self.event
        return context


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'registration/sign_up.html'
    success_url = '/'
