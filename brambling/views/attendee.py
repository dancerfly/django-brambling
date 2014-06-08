import json

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, View, UpdateView
import floppyforms.__future__ as forms

from brambling.forms.attendee import (UsedDiscountForm, CheckoutForm,
                                      HostingForm, AttendeeBasicDataForm,
                                      AttendeeHousingDataForm)
from brambling.models import (Item, BoughtItem, ItemOption, Payment,
                              UsedDiscount, Discount, EventPerson,
                              Attendee, EventHousing)
from brambling.views.utils import (get_event_or_404, get_event_nav,
                                   get_event_admin_nav, ajax_required)


class AddToCartView(View):
    @method_decorator(ajax_required)
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        event = get_event_or_404(kwargs['event_slug'])
        try:
            item_option = ItemOption.objects.get(item__event=event,
                                                 pk=kwargs['pk'])
        except ItemOption.DoesNotExist:
            raise Http404

        event_person = EventPerson.objects.get_cached(event, request.user)
        event_person.add_to_cart(item_option)
        return JsonResponse({'success': True})


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
            event_person = EventPerson.objects.get_cached(event, request.user)
            event_person.remove_from_cart(bought_item)

        return JsonResponse({'success': True})


class UseDiscountView(View):
    @method_decorator(ajax_required)
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        event = get_event_or_404(kwargs['event_slug'])

        form = UsedDiscountForm(
            event=event,
            person=request.user,
            prefix='discount-form',
            data=json.loads(request.body),
        )

        if form.is_valid():
            instance = form.save()
            return JsonResponse({
                'success': True,
                'name': instance.discount.name,
                'code': instance.discount.code,
            })

        return JsonResponse({
            'success': False,
            'errors': form.errors,
        })


# Registration works like this:
# 1. Shop. Choose things.
# 2. Who are these for? <- part of shop?
# 3. Any relevant EventPerson fields <- Registration information. one page per pass.
# 4. If housing is enabled, one page per pass that requests or offers housing.
# 5. Checkout - unpaid items only. List any applicable credits without explanation.


def _shared_shopping_context(event, request):
    event_person = EventPerson.objects.get_cached(event, request.user)
    return {
        'event': event,
        'event_person': event_person,
        'discount_form': UsedDiscountForm(event=event,
                                          person=request.user,
                                          prefix='discount-form'),
        'discounts': event_person.useddiscount_set.all(),
        'event_nav': get_event_nav(event, request),
        'event_admin_nav': get_event_admin_nav(event, request),
    }


class ShopView(TemplateView):
    categories = (
        Item.MERCHANDISE,
        Item.COMPETITION,
        Item.CLASS,
        Item.PASS
    )
    template_name = 'brambling/event/shop.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ShopView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ShopView, self).get_context_data(**kwargs)

        event = get_event_or_404(self.kwargs['event_slug'])
        now = timezone.now()
        items = event.items.filter(
            options__available_start__lte=now,
            options__available_end__gte=now,
            category__in=self.categories,
        ).select_related('options').distinct()

        context.update({
            'items': items,
        })
        context.update(_shared_shopping_context(event, self.request))
        return context


class AttendeeItemView(TemplateView):
    template_name = 'brambling/event/attendee_items.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.event = get_event_or_404(kwargs['event_slug'])
        self.event_person = EventPerson.objects.get_cached(self.event, request.user)
        return super(AttendeeItemView, self).dispatch(request, *args, **kwargs)

    def get_forms(self):
        form_class = forms.models.modelform_factory(BoughtItem, fields=('attendee',))
        form_class.base_fields['attendee'].queryset = self.event_person.attendees.all()
        form_class.base_fields['attendee'].required = True
        bought_items = self.event_person.bought_items.all()
        kwargs = {}
        if self.request.method == 'POST':
            kwargs['data'] = self.request.POST
        self.attendees = self.event_person.attendees.all()
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
        })
        context.update(_shared_shopping_context(self.event, self.request))
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
        self.event_person = EventPerson.objects.get_cached(self.event, request.user)
        return super(AttendeeBasicDataView, self).dispatch(request, *args, **kwargs)

    def get_object(self):
        if self.kwargs.get('pk') is None:
            return None
        else:
            return self.event_person.attendees.get(pk=self.kwargs['pk'])

    def get_initial(self):
        initial = super(AttendeeBasicDataView, self).get_initial()
        person = self.request.user
        if not self.event_person.attendees.filter(person=person).exists():
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

        form.instance.event_person = self.event_person
        form.instance.basic_completed = True
        self.object = form.save()
        return super(AttendeeBasicDataView, self).form_valid(form)

    def get_success_url(self):
        return reverse('brambling_event_attendee_items',
                       kwargs={'event_slug': self.event.slug})

    def get_context_data(self, **kwargs):
        context = super(AttendeeBasicDataView, self).get_context_data(**kwargs)
        context.update({
            'attendees': self.event_person.attendees.all(),
        })
        context.update(_shared_shopping_context(self.event, self.request))
        return context


class RemoveAttendeeView(View):
    @method_decorator(ajax_required)
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        event = get_event_or_404(kwargs['event_slug'])
        Attendee.objects.filter(event_person__event=event,
                                pk=kwargs['pk']).delete()

        return JsonResponse({'success': True})


class AttendeeHousingView(TemplateView):
    template_name = 'brambling/event/attendee_housing.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.event = get_event_or_404(kwargs['event_slug'])
        self.event_person = EventPerson.objects.get_cached(self.event, request.user)
        self.attendees = self.event_person.attendees.filter(housing_status=Attendee.NEED)
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
        context.update(_shared_shopping_context(self.event, self.request))
        return context


class SurveyDataView(UpdateView):
    template_name = 'brambling/event/survey_data.html'
    fields = ('heard_through', 'heard_through_other', 'send_flyers',
              'send_flyers_address', 'send_flyers_city',
              'send_flyers_state_or_province', 'send_flyers_country',
              'providing_housing')
    context_object_name = 'event_person'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.event = get_event_or_404(kwargs['event_slug'])
        return super(SurveyDataView, self).dispatch(request, *args, **kwargs)

    def get_form_class(self):
        return forms.models.modelform_factory(EventPerson, fields=self.fields)

    def get_object(self):
        return EventPerson.objects.get_cached(self.event, self.request.user)

    def get_context_data(self, **kwargs):
        context = super(SurveyDataView, self).get_context_data(**kwargs)
        context.update(_shared_shopping_context(self.event, self.request))
        return context

    def form_valid(self, form):
        self.object.survey_completed = True
        self.object.save()
        form.save()
        return HttpResponseRedirect(reverse('brambling_event_records',
                                            kwargs={'event_slug': self.event.slug}))


class HostingView(UpdateView):
    template_name = 'brambling/event/hosting.html'
    form_class = HostingForm

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.event = get_event_or_404(kwargs['event_slug'])
        self.event_person = EventPerson.objects.get_cached(self.event, request.user)
        return super(HostingView, self).dispatch(request, *args, **kwargs)

    def get_object(self):
        try:
            return EventHousing.objects.select_related('home').get(
                event=self.event,
                event_person=self.event_person,
            )
        except EventHousing.DoesNotExist:
            return EventHousing(
                event=self.event,
                event_person=self.event_person,
                home=self.event_person.person.home
            )

    def get_context_data(self, **kwargs):
        context = super(HostingView, self).get_context_data(**kwargs)

        context.update(_shared_shopping_context(self.event, self.request))

        return context

    def get_success_url(self):
        return reverse('brambling_event_records',
                       kwargs={'event_slug': self.event.slug})


class RecordsView(TemplateView):
    template_name = 'brambling/event/records.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.event = get_event_or_404(kwargs['event_slug'])
        self.event_person = EventPerson.objects.get_cached(self.event, request.user)
        self.balance = self.get_balance()
        return super(RecordsView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if self.balance > 0 or self.event_person.has_cart():
            self.form = self.get_form()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        if self.balance > 0 or self.event_person.has_cart():
            self.form = self.get_form()
            if self.form.is_valid():
                self.form.save()
                # Mark reserved / unpaid items as paid.
                self.event_person.bought_items.filter(
                    status__in=(BoughtItem.RESERVED, BoughtItem.UNPAID)
                ).update(status=BoughtItem.PAID)
                if self.event_person.cart_start_time is not None:
                    self.event_person.cart_start_time = None
                    self.event_person.save()
                return HttpResponseRedirect('')
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_form(self):
        kwargs = {
            'person': self.request.user,
            'event': self.event,
            'balance': self.balance,
        }
        if self.request.method == 'POST':
            kwargs['data'] = self.request.POST
        return CheckoutForm(**kwargs)

    def get_balance(self):
        self.payments = Payment.objects.filter(
            event_person=self.event_person,
        ).order_by('timestamp')
        self.personitems = BoughtItem.objects.filter(
            event_person=self.event_person,
        ).order_by('added')

        self.discounts = UsedDiscount.objects.filter(
            event_person=self.event_person,
        ).select_related('discount').order_by('timestamp')

        discount_map = {}

        for discount in self.discounts:
            discount_map.setdefault(discount.discount.item_option_id, []).append(discount)
        savings = 0
        for item in self.personitems:
            if item.item_option_id not in discount_map:
                continue
            discounts = discount_map[item.item_option_id]
            for discount in discounts:
                amount = (discount.discount.amount
                          if discount.discount.discount_type == Discount.FLAT
                          else discount.discount.amount / 100 * discount.discount.item_option.price)
                if not hasattr(discount, 'items'):
                    discount.items = []
                discount.items.append((item, amount))
                savings += amount

        self.total_cost = sum((item.item_option.price
                               for item in self.personitems))
        self.total_savings = min(savings, self.total_cost)
        self.total_payments = sum((payment.amount
                                   for payment in self.payments))
        return self.total_cost - self.total_savings - self.total_payments

    def get_context_data(self, **kwargs):
        context = super(RecordsView, self).get_context_data(**kwargs)

        context.update(_shared_shopping_context(self.event, self.request))

        context.update({
            'form': getattr(self, 'form', None),
            'personitems': self.personitems,
            'payments': self.payments,
            'discounts': self.discounts,
            'total_cost': self.total_cost,
            'total_savings': self.total_savings,
            'total_payments': self.total_payments,
            'balance': self.balance,
        })
        return context
