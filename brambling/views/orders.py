from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db.models import Count, Q, F
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, View, UpdateView
import floppyforms.__future__ as forms

from brambling.forms.orders import (SavedCardPaymentForm, OneTimePaymentForm,
                                    HostingForm, AttendeeBasicDataForm,
                                    AttendeeHousingDataForm)
from brambling.models import (Item, BoughtItem, ItemOption, Payment,
                              BoughtItemDiscount, Discount, Order,
                              Attendee, EventHousing)
from brambling.views.utils import (get_event_or_404, get_event_nav,
                                   get_event_admin_nav, ajax_required,
                                   get_order, clear_expired_carts)


class AddToCartView(View):
    @method_decorator(ajax_required)
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        event = get_event_or_404(kwargs['event_slug'])
        clear_expired_carts(event)
        try:
            item_option = ItemOption.objects.annotate(taken=Count('boughtitem')
                                           ).get(item__event=event,
                                                 pk=kwargs['pk'])
        except ItemOption.DoesNotExist:
            raise Http404

        if item_option.taken >= item_option.total_number:
            return JsonResponse({'success': False, 'error': 'That item is sold out.'})

        order = get_order(event, request.user)
        if order.person.confirmed_email:
            order.add_to_cart(item_option)
            return JsonResponse({'success': True})
        return JsonResponse({'success': False})


class RemoveFromCartView(View):
    @method_decorator(ajax_required)
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        event = get_event_or_404(kwargs['event_slug'])
        try:
            bought_item = BoughtItem.objects.get(item_option__item__event=event,
                                                 pk=kwargs['pk'])
        except BoughtItem.DoesNotExist:
            pass
        else:
            order = get_order(event, request.user)
            order.remove_from_cart(bought_item)

        return JsonResponse({'success': True})


class UseDiscountView(View):
    @method_decorator(ajax_required)
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        event = get_event_or_404(kwargs['event_slug'])
        now = timezone.now()
        try:
            discount = Discount.objects.filter(
                code=kwargs['discount'],
                event=event
            ).filter(
                (Q(available_start__lte=now) |
                 Q(available_start__isnull=True)),
                (Q(available_end__gte=now) |
                 Q(available_end__isnull=True))
            ).get()
        except Discount.DoesNotExist:
            return JsonResponse({
                'success': False,
                'errors': {
                    'discount': ("No discount with that code is currently "
                                 "active for this event.")
                },
            })

        order = get_order(event, request.user)
        created = order.add_discount(discount)
        if created:
            return JsonResponse({
                'success': True,
                'name': discount.name,
                'code': discount.code,
            })
        return JsonResponse({
            'success': True,
        })


# Registration works like this:
# 1. Shop. Choose things.
# 2. Who are these for? <- part of shop?
# 3. Any relevant Order fields <- Registration information. one page per pass.
# 4. If housing is enabled, one page per pass that requests or offers housing.
# 5. Checkout - unpaid items only. List any applicable credits without explanation.


def _shared_shopping_context(request, order):
    event = order.event
    return {
        'event': event,
        'order': order,
        'discounts': order.discounts.all(),
        'event_nav': get_event_nav(event, request),
        'event_admin_nav': get_event_admin_nav(event, request),
    }


class ShopView(TemplateView):
    template_name = 'brambling/event/shop.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ShopView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ShopView, self).get_context_data(**kwargs)

        event = get_event_or_404(self.kwargs['event_slug'])
        clear_expired_carts(event)
        now = timezone.now()
        item_options = ItemOption.objects.filter(
            available_start__lte=now,
            available_end__gte=now,
            item__event=event,
        ).annotate(taken=Count('boughtitem')).filter(
            total_number__gt=F('taken')
        ).order_by('item')

        context.update({
            'item_options': item_options,
        })
        order = get_order(event, self.request.user)
        order.event = event
        context.update(_shared_shopping_context(self.request, order))
        return context


class AttendeeItemView(TemplateView):
    template_name = 'brambling/event/attendee_items.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.event = get_event_or_404(kwargs['event_slug'])
        self.order = get_order(self.event, request.user)
        self.errors = []
        return super(AttendeeItemView, self).dispatch(request, *args, **kwargs)

    def get_forms(self):
        form_class = forms.models.modelform_factory(BoughtItem, fields=('attendee',))
        form_class.base_fields['attendee'].queryset = self.order.attendees.all()
        form_class.base_fields['attendee'].required = True
        bought_items = self.order.bought_items.order_by('item_option__item', 'item_option')
        kwargs = {}
        if self.request.method == 'POST':
            kwargs['data'] = self.request.POST
        self.attendees = self.order.attendees.all()
        if len(self.attendees) == 1:
            kwargs['initial'] = {'attendee': self.attendees[0]}
        return [form_class(prefix='form-{}-'.format(item.pk),
                           instance=item, **kwargs)
                for item in bought_items]

    def get(self, request, *args, **kwargs):
        self.forms = self.get_forms()
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        self.forms = self.get_forms()
        all_valid = True
        for form in self.forms:
            all_valid = all_valid and form.is_valid()
        if all_valid:
            for form in self.forms:
                form.save()

            attendees = self.attendees.filter(
                bought_items__item_option__item__category=Item.PASS
            ).distinct().annotate(
                Count('bought_items')
            ).filter(
                bought_items__count__gte=2
            )
            if attendees:
                all_valid = False
                for attendee in attendees:
                    self.errors.append('{} may not have more than one pass'.format(attendee.name))

        if all_valid:
            if self.event.collect_housing_data:
                url = reverse('brambling_event_attendee_housing',
                              kwargs={'event_slug': self.event.slug})
            else:
                url = reverse('brambling_event_survey',
                              kwargs={'event_slug': self.event.slug})
            return HttpResponseRedirect(url)
        return self.render_to_response(self.get_context_data())

    def get_context_data(self, **kwargs):
        context = super(AttendeeItemView, self).get_context_data(**kwargs)

        context.update({
            'forms': self.forms,
            'attendees': self.attendees,
            'errors': self.errors,
        })
        context.update(_shared_shopping_context(self.request, self.order))
        return context


class AttendeeBasicDataView(UpdateView):
    template_name = 'brambling/event/attendee_basic_data.html'
    form_class = AttendeeBasicDataForm

    def get_form_class(self):
        fields = ('name', 'nickname', 'email', 'phone', 'liability_waiver',
                  'photo_consent')
        if self.event.collect_housing_data:
            fields += ('housing_status',)
        return forms.models.modelform_factory(Attendee, self.form_class, fields=fields)

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.event = get_event_or_404(kwargs['event_slug'])
        self.order = get_order(self.event, request.user)
        return super(AttendeeBasicDataView, self).dispatch(request, *args, **kwargs)

    def get_object(self):
        if self.kwargs.get('pk') is None:
            return None
        else:
            return self.order.attendees.get(pk=self.kwargs['pk'])

    def get_initial(self):
        initial = super(AttendeeBasicDataView, self).get_initial()
        person = self.request.user
        if not self.order.attendees.filter(person=person).exists():
            initial.update({
                'name': person.name,
                'nickname': person.nickname,
                'email': person.email,
                'phone': person.phone
            })
        return initial

    def form_valid(self, form):
        if form.instance.email == self.request.user.email:
            form.instance.person = self.request.user
            form.instance.person_confirmed = True

        form.instance.order = self.order
        form.instance.basic_completed = True
        self.object = form.save()
        return super(AttendeeBasicDataView, self).form_valid(form)

    def get_success_url(self):
        return reverse('brambling_event_attendee_items',
                       kwargs={'event_slug': self.event.slug})

    def get_context_data(self, **kwargs):
        context = super(AttendeeBasicDataView, self).get_context_data(**kwargs)
        context.update({
            'attendees': self.order.attendees.all(),
        })
        context.update(_shared_shopping_context(self.request, self.order))
        return context


class RemoveAttendeeView(View):
    @method_decorator(ajax_required)
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        event = get_event_or_404(kwargs['event_slug'])
        Attendee.objects.filter(order__event=event,
                                pk=kwargs['pk']).delete()

        return JsonResponse({'success': True})


class AttendeeHousingView(TemplateView):
    template_name = 'brambling/event/attendee_housing.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.event = get_event_or_404(kwargs['event_slug'])
        self.order = get_order(self.event, request.user)
        self.attendees = self.order.attendees.filter(housing_status=Attendee.NEED)
        if not self.event.collect_housing_data or not self.attendees:
            # Just skip ahead.
            return HttpResponseRedirect(reverse('brambling_event_survey',
                                        kwargs={'event_slug': self.event.slug}))
        return super(AttendeeHousingView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.forms = self.get_forms()
        if not self.forms:
            return HttpResponseRedirect(self.get_success_url())
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.forms = self.get_forms()
        all_valid = True
        for form in self.forms:
            if not form.is_valid():
                all_valid = False
        if all_valid:
            for form in self.forms:
                form.save()
            return HttpResponseRedirect(self.get_success_url())
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_success_url(self):
        return reverse('brambling_event_survey',
                       kwargs={'event_slug': self.event.slug})

    def get_forms(self):
        memo_dict = {}
        kwargs = {
            'memo_dict': memo_dict,
        }
        if self.request.method == 'POST':
            kwargs['data'] = self.request.POST

        return [AttendeeHousingDataForm(prefix='form-{}-'.format(attendee.pk),
                                        instance=attendee,
                                        **kwargs)
                for attendee in self.attendees]

    def get_context_data(self, **kwargs):
        context = super(AttendeeHousingView, self).get_context_data(**kwargs)

        context.update({
            'event': self.event,
            'forms': self.forms,
        })
        context.update(_shared_shopping_context(self.request, self.order))
        return context


class SurveyDataView(UpdateView):
    template_name = 'brambling/event/survey_data.html'
    context_object_name = 'order'

    @property
    def fields(self):
        fields = ()
        if self.event.collect_housing_data:
            fields += ('providing_housing',)
        if self.event.collect_survey_data:
            fields += ('heard_through', 'heard_through_other', 'send_flyers',
                       'send_flyers_address', 'send_flyers_city',
                       'send_flyers_state_or_province', 'send_flyers_country')
        return fields

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.event = get_event_or_404(kwargs['event_slug'])
        if not self.fields:
            return HttpResponseRedirect(self.get_success_url())
        return super(SurveyDataView, self).dispatch(request, *args, **kwargs)

    def get_form_class(self):
        return forms.models.modelform_factory(Order, fields=self.fields)

    def get_object(self):
        return get_order(self.event, self.request.user)

    def get_context_data(self, **kwargs):
        context = super(SurveyDataView, self).get_context_data(**kwargs)
        context.update(_shared_shopping_context(self.request, self.object))
        return context

    def form_valid(self, form):
        if self.event.collect_survey_data:
            self.object.survey_completed = True
        form.save()
        return super(SurveyDataView, self).form_valid(form)

    def get_success_url(self):
        kwargs = {'event_slug': self.event.slug}
        if self.event.collect_housing_data and self.object.providing_housing:
            return reverse('brambling_event_hosting', kwargs=kwargs)
        return reverse('brambling_event_order_summary', kwargs=kwargs)


class HostingView(UpdateView):
    template_name = 'brambling/event/hosting.html'
    form_class = HostingForm

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.event = get_event_or_404(kwargs['event_slug'])
        if not self.event.collect_housing_data:
            return HttpResponseRedirect(self.get_success_url())
        self.order = get_order(self.event, request.user)
        return super(HostingView, self).dispatch(request, *args, **kwargs)

    def get_object(self):
        try:
            return EventHousing.objects.select_related('home').get(
                event=self.event,
                order=self.order,
            )
        except EventHousing.DoesNotExist:
            return EventHousing(
                event=self.event,
                order=self.order,
                home=self.order.person.home
            )

    def get_context_data(self, **kwargs):
        context = super(HostingView, self).get_context_data(**kwargs)

        context.update(_shared_shopping_context(self.request, self.order))

        return context

    def get_success_url(self):
        return reverse('brambling_event_order_summary',
                       kwargs={'event_slug': self.event.slug})


class OrderSummaryView(TemplateView):
    template_name = 'brambling/event/records.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.event = get_event_or_404(kwargs['event_slug'])
        self.order = get_order(self.event, request.user)
        self.balance = self.get_balance()
        return super(OrderSummaryView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if self.balance > 0 or self.order.has_cart():
            self.get_forms()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        if self.balance == 0:
            self.order.mark_cart_paid()
        else:
            self.get_forms()
            form = None
            if 'choose_card' in request.POST:
                # Get a choose form.
                form = self.choose_card_form
            if 'new_card' in request.POST:
                # Get a new form.
                form = self.new_card_form
            if form and form.is_valid():
                form.save()
                self.order.mark_cart_paid()
                return HttpResponseRedirect('')
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_forms(self):
        kwargs = {
            'order': self.order,
            'amount': self.balance,
        }
        choose_data = None
        new_data = None
        if self.request.method == 'POST':
            if 'choose_card' in self.request.POST:
                choose_data = self.request.POST
            elif 'new_card' in self.request.POST:
                new_data = self.request.POST
        self.choose_card_form = SavedCardPaymentForm(data=choose_data, **kwargs)
        self.new_card_form = OneTimePaymentForm(data=new_data, user=self.request.user, **kwargs)

    def get_balance(self):
        self.payments = Payment.objects.filter(
            order=self.order,
        ).order_by('timestamp')
        self.bought_items = list(BoughtItem.objects.filter(
            order=self.order,
        ).select_related('item_option').order_by('added'))

        self.discounts = BoughtItemDiscount.objects.filter(
            bought_item__in=self.bought_items,
        ).select_related('discount').order_by('discount', 'timestamp')

        bought_item_map = {bought_item.id: bought_item
                           for bought_item in self.bought_items}
        savings = 0
        for discount in self.discounts:
            try:
                bought_item = bought_item_map[discount.bought_item_id]
            except KeyError:
                continue
            discount.bought_item = bought_item
            savings += discount.savings()

        self.total_cost = sum((item.item_option.price
                               for item in self.bought_items))
        self.total_savings = min(savings, self.total_cost)
        self.total_payments = sum((payment.amount
                                   for payment in self.payments))
        return self.total_cost - self.total_savings - self.total_payments

    def get_context_data(self, **kwargs):
        context = super(OrderSummaryView, self).get_context_data(**kwargs)

        context.update(_shared_shopping_context(self.request, self.order))

        context.update({
            'has_cards': self.order.person.cards.exists(),
            'new_card_form': getattr(self, 'new_card_form', None),
            'choose_card_form': getattr(self, 'choose_card_form', None),
            'bought_items': self.bought_items,
            'payments': self.payments,
            'discounts': self.discounts,
            'total_cost': self.total_cost,
            'total_savings': self.total_savings,
            'total_payments': self.total_payments,
            'balance': self.balance,
            'STRIPE_PUBLISHABLE_KEY': getattr(settings,
                                              'STRIPE_PUBLISHABLE_KEY',
                                              ''),
        })
        return context
