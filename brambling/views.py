from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db.models import Q, Max, Min, Count
from django.utils.decorators import method_decorator
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils import timezone
from django.utils.http import urlsafe_base64_decode
from django.views.generic import (ListView, DetailView, CreateView, UpdateView,
                                  TemplateView, View)
from zenaida.forms import modelform_factory, modelformset_factory

from brambling.forms import (EventForm, PersonForm, HomeForm, ItemForm,
                             ItemOptionFormSet, DiscountForm, SignUpForm,
                             ReservationForm, GuestForm, HostingForm,
                             EventPersonForm, PersonItemForm,
                             PersonItemFormSet, PersonDiscountForm)
from brambling.models import (Event, Person, Home, Item, Discount, EventPerson,
                              EventHousing, PersonItem)
from brambling.tokens import token_generators
from brambling.utils import send_confirmation_email


def home(request):
    if request.user.is_authenticated():
        return Dashboard.as_view()(request)
    else:
        return EventListView.as_view()(request)


class Dashboard(TemplateView):
    template_name = "brambling/dashboard.html"

    def get_context_data(self):
        user = self.request.user
        today = timezone.now().date()

        upcoming_events = Event.objects.filter(
            privacy=Event.PUBLIC,
            dance_style__person=user,
            event_type__person=user
        ).annotate(start_date=Min('dates__date')
                   ).filter(start_date__gte=today).order_by('start_date')

        admin_events = Event.objects.filter(
            (Q(owner=user) | Q(editors=user)),
        ).order_by('-last_modified')

        registered_events = Event.objects.filter(
            eventperson__person=user,
        ).annotate(start_date=Min('dates__date')
                   ).filter(start_date__gte=today).order_by('-start_date')
        return {
            'upcoming_events': upcoming_events,
            'admin_events': admin_events,
            'registered_events': registered_events,
        }

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(Dashboard, self).dispatch(*args, **kwargs)


class EventListView(ListView):
    model = Event
    template_name = 'brambling/event/list.html'
    context_object_name = 'events'

    def get_queryset(self):
        qs = super(EventListView, self).get_queryset()
        return qs.filter(privacy=Event.PUBLIC)


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


def _get_event_or_404(slug):
    qs = Event.objects.annotate(start_date=Min('dates__date'),
                                end_date=Max('dates__date'))
    return get_object_or_404(qs, slug=slug)


class EventUpdateView(UpdateView):
    model = Event
    template_name = 'brambling/event/update.html'
    context_object_name = 'event'
    form_class = EventForm

    def get_object(self):
        obj = _get_event_or_404(self.kwargs['slug'])
        user = self.request.user
        if not obj.can_edit(user):
            raise Http404
        return obj

    def get_context_data(self, **kwargs):
        context = super(EventUpdateView, self).get_context_data(**kwargs)
        context['cart_total'] = self.request.user.get_cart_total(self.object)
        return context


class HomeView(UpdateView):
    model = Home
    form_class = HomeForm

    def get_object(self):
        if not self.request.user.is_authenticated():
            raise Http404
        return (Home.objects.filter(residents=self.request.user).first() or
                Home())

    def get_form_kwargs(self):
        kwargs = super(HomeView, self).get_form_kwargs()
        kwargs['person'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('brambling_home')


def item_form(request, *args, **kwargs):
    event = _get_event_or_404(kwargs['event_slug'])
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
        'cart_total': request.user.get_cart_total(event),
    }
    return render_to_response('brambling/event/item_form.html',
                              context,
                              context_instance=RequestContext(request))


class ItemListView(ListView):
    model = Item
    context_object_name = 'items'
    template_name = 'brambling/event/item_list.html'

    def get_queryset(self):
        self.event = _get_event_or_404(self.kwargs['event_slug'])
        if not self.event.can_edit(self.request.user):
            raise Http404
        qs = super(ItemListView, self).get_queryset()
        return qs.filter(event=self.event
                         ).annotate(option_count=Count('options'))

    def get_context_data(self, **kwargs):
        context = super(ItemListView, self).get_context_data(**kwargs)
        context['event'] = self.event
        context['cart_total'] = self.request.user.get_cart_total(self.event)
        return context


def discount_form(request, *args, **kwargs):
    event = _get_event_or_404(kwargs['event_slug'])
    if not event.can_edit(request.user):
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
        'cart_total': request.user.get_cart_total(event),
    }
    return render_to_response('brambling/event/discount_form.html',
                              context,
                              context_instance=RequestContext(request))


class DiscountListView(ListView):
    model = Discount
    context_object_name = 'discounts'
    template_name = 'brambling/event/discount_list.html'

    def get_queryset(self):
        self.event = _get_event_or_404(self.kwargs['event_slug'])
        if not self.event.can_edit(self.request.user):
            raise Http404
        qs = super(DiscountListView, self).get_queryset()
        return qs.filter(event=self.event)

    def get_context_data(self, **kwargs):
        context = super(DiscountListView, self).get_context_data(**kwargs)
        context['event'] = self.event
        context['cart_total'] = self.request.user.get_cart_total(self.event)
        return context


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'registration/sign_up.html'
    success_url = '/'

    def get_form_kwargs(self):
        kwargs = super(SignUpView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class PersonView(UpdateView):
    model = Person
    form_class = PersonForm

    def get_object(self):
        if self.request.user.is_authenticated():
            return self.request.user
        raise Http404

    def get_form_kwargs(self):
        kwargs = super(PersonView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_success_url(self):
        return self.request.path


def send_confirmation_email_view(request, *args, **kwargs):
    if not request.user.is_authenticated():
        raise Http404
    send_confirmation_email(request.user, request, secure=request.is_secure())
    messages.add_message(request, messages.SUCCESS, "Confirmation email sent.")
    return HttpResponseRedirect('/')


class EmailConfirmView(DetailView):
    model = Person
    generator = token_generators['email_confirm']
    template_name = 'brambling/email_confirm.html'

    def get_object(self):
        if 'pkb64' not in self.kwargs:
            raise AttributeError("pkb64 required.")
        try:
            pk = urlsafe_base64_decode(self.kwargs['pkb64'])
            return Person._default_manager.get(pk=pk)
        except (TypeError, ValueError, OverflowError, Person.DoesNotExist):
            raise Http404

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.generator.check_token(self.object, self.kwargs['token']):
            raise Http404("Token invalid or expired.")
        self.object.confirmed_email = self.object.email
        self.object.save()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class EventDetailView(DetailView):
    model = Event
    template_name = 'brambling/event/detail.html'
    context_object_name = 'event'

    def get_object(self):
        obj = _get_event_or_404(self.kwargs['slug'])
        if obj.privacy == Event.PRIVATE:
            user = self.request.user
            if not obj.can_edit(user):
                raise Http404
        return obj

    def get_queryset(self):
        queryset = super(EventDetailView, self).get_queryset()
        return queryset.prefetch_related('editors')

    def get_context_data(self, **kwargs):
        context = super(EventDetailView, self).get_context_data(**kwargs)
        context['cart_total'] = self.request.user.get_cart_total(self.object)
        return context


class ReservationView(TemplateView):
    categories = (
        Item.MERCHANDISE,
        Item.COMPETITION,
        Item.CLASS,
        Item.PASS
    )
    template_name = 'brambling/event/reserve.html'

    def get_items(self):
        now = timezone.now()
        return self.event.items.filter(
            options__available_start__lte=now,
            options__available_end__gte=now,
            category__in=self.categories,
        ).select_related('options').distinct()

    def get_form_kwargs(self, option):
        kwargs = {
            'buyer': self.request.user,
            'item_option': option,
            'prefix': str(option.pk),
        }
        if self.request.method == 'POST':
            kwargs['data'] = self.request.POST
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(ReservationView, self).get_context_data(**kwargs)
        items = tuple((item, [ReservationForm(**self.get_form_kwargs(option))
                              for option in item.options.all()])
                      for item in self.items)

        discount_form_kwargs = {
            'event': self.event,
            'person': self.request.user,
            'prefix': 'discount-form'
        }
        if self.request.method == 'POST':
            discount_form_kwargs['data'] = self.request.POST

        context.update({
            'event': self.event,
            'items': items,
            'discount_form': PersonDiscountForm(**discount_form_kwargs),
            'cart': self.request.user.get_cart(self.event),
            'cart_total': self.request.user.get_cart_total(self.event),
            'discounts': self.request.user.get_discounts(self.event),
        })
        return context

    def get(self, request, *args, **kwargs):
        self.event = _get_event_or_404(kwargs['slug'])
        self.items = self.get_items()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.event = _get_event_or_404(kwargs['slug'])
        self.items = self.get_items()
        context = self.get_context_data(**kwargs)
        saved = False
        for item, form_list in context['items']:
            for form in form_list:
                if form.is_valid():
                    form.save()
                    saved = True
        if context['discount_form'].is_valid():
            context['discount_form'].save()
            saved = True
        if saved:
            return HttpResponseRedirect(request.path)
        return self.render_to_response(context)


class CartView(TemplateView):
    template_name = 'brambling/event/cart.html'

    def get(self, request, *args, **kwargs):
        self.event = _get_event_or_404(kwargs['slug'])
        self.formset = self.get_formset()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.event = _get_event_or_404(kwargs['slug'])
        self.formset = self.get_formset()
        if self.formset.is_valid():
            self.formset.save()
            return HttpResponseRedirect('')
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_formset(self):
        reservation_start = (timezone.now() -
                             timedelta(minutes=self.event.reservation_timeout))
        items = PersonItem.objects.filter(
            ((Q(status=PersonItem.RESERVED) &
              Q(added__gte=reservation_start)) |
             ~Q(status=PersonItem.RESERVED)) &
            (Q(buyer=self.request.user) | Q(owner=self.request.user)) &
            Q(item_option__item__event=self.event)
            ).select_related('item_option__item').order_by('-added')
        formset_class = modelformset_factory(PersonItem, PersonItemForm,
                                             formset=PersonItemFormSet, extra=0)

        kwargs = {
            'queryset': items,
            'event': self.event,
            'user': self.request.user,
        }
        if self.request.method == 'POST':
            kwargs['data'] = self.request.POST
        return formset_class(**kwargs)

    def get_context_data(self, **kwargs):
        context = super(CartView, self).get_context_data(**kwargs)

        context.update({
            'event': self.event,
            'cart_total': self.request.user.get_cart_total(self.event),
            'formset': self.formset,
            'discounts': self.request.user.get_discounts(self.event),
        })
        context['formset'].forms
        return context
