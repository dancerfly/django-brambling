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
from brambling.models import (Item, BoughtItem, ItemOption,
                              BoughtItemDiscount, Discount, Order,
                              Attendee, EventHousing)
from brambling.views.utils import (get_event_or_404, get_event_admin_nav,
                                   ajax_required, get_order,
                                   clear_expired_carts)


class OrderMixin(object):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        self.event = get_event_or_404(kwargs['event_slug'])
        if 'code' in self.kwargs:
            self.order = get_order(self.event, code=self.kwargs['code'])
            if (not self.order.person == self.request.user and
                    not self.is_admin_request):
                raise Http404
        else:
            self.order = get_order(self.event, self.request.user)
        return super(OrderMixin, self).dispatch(*args, **kwargs)

    @property
    def is_admin_request(self):
        if not hasattr(self, '_is_admin_request'):
            self._is_admin_request = self.event.editable_by(self.request.user)
        return self._is_admin_request

    def get_context_data(self, **kwargs):
        context = super(OrderMixin, self).get_context_data(**kwargs)
        context.update({
            'event': self.event,
            'order': self.order,
            'event_admin_nav': get_event_admin_nav(self.event, self.request),
            'is_admin_request': self.is_admin_request,
        })
        return context


class AddToOrderView(OrderMixin, View):
    @method_decorator(ajax_required)
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        clear_expired_carts(self.event)

        try:
            item_option = ItemOption.objects.annotate(taken=Count('boughtitem')
                                           ).get(item__event=self.event,
                                                 pk=kwargs['pk'])
        except ItemOption.DoesNotExist:
            raise Http404

        if item_option.taken >= item_option.total_number:
            return JsonResponse({'success': False, 'error': 'That item is sold out.'})

        if self.order.person.confirmed_email or self.is_admin_request:
            self.order.add_to_cart(item_option)
            return JsonResponse({'success': True})
        return JsonResponse({'success': False})


class RemoveFromOrderView(View):
    @method_decorator(ajax_required)
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        try:
            bought_item = BoughtItem.objects.get(item_option__item__event=event,
                                                 pk=kwargs['pk'])
        except BoughtItem.DoesNotExist:
            pass
        else:
            self.order.remove_from_cart(bought_item)

        return JsonResponse({'success': True})


class ApplyDiscountView(OrderMixin, View):
    @method_decorator(ajax_required)
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):

        discounts = Discount.objects.filter(
            code=kwargs['discount'],
            event=self.event
        )
        if self.is_admin_request:
            try:
                discount = discounts.get()
            except Discount.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'errors': {
                        'discount': ("No discount with that code exists "
                                     "for this event.")
                    },
                })
        else:
            now = timezone.now()
            try:
                discounts = discounts.filter(
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

        created = order.add_discount(discount, force=self.is_admin_request)
        if created:
            return JsonResponse({
                'success': True,
                'name': discount.name,
                'code': discount.code,
            })
        return JsonResponse({
            'success': True,
        })


class RemoveDiscountView(OrderMixin, View):
    @method_decorator(ajax_required)
    @method_decorator(login_required)
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


class ChooseItemsView(OrderMixin, TemplateView):
    template_name = 'brambling/event/shop.html'

    def get_context_data(self, **kwargs):
        context = super(ChooseItemsView, self).get_context_data(**kwargs)
        clear_expired_carts(self.event)
        now = timezone.now()
        item_options = ItemOption.objects.filter(
            available_start__lte=now,
            available_end__gte=now,
            item__event=self.event,
        ).annotate(taken=Count('boughtitem')).filter(
            total_number__gt=F('taken')
        ).order_by('item')

        context['item_options'] = item_options
        return context


class AttendeeItemView(OrderMixin, TemplateView):
    template_name = 'brambling/event/attendee_items.html'

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
        self.errors = []
        self.forms = self.get_forms()
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        self.errors = []
        self.forms = self.get_forms()
        all_valid = True
        for form in self.forms:
            all_valid = all_valid and form.is_valid()
        if all_valid:
            for form in self.forms:
                form.save()

            self.errors = self.order.steps()['attendees']['errors']

        if all_valid and not self.errors:
            url = self.order.steps().values()[2]['url']
            return HttpResponseRedirect(url)
        return self.render_to_response(self.get_context_data())

    def get_context_data(self, **kwargs):
        context = super(AttendeeItemView, self).get_context_data(**kwargs)

        context.update({
            'forms': self.forms,
            'attendees': self.attendees,
            'errors': self.errors,
        })
        return context


class AttendeeBasicDataView(OrderMixin, UpdateView):
    template_name = 'brambling/event/attendee_basic_data.html'
    form_class = AttendeeBasicDataForm

    def get_form_class(self):
        fields = ('given_name', 'middle_name', 'surname', 'name_order', 'email',
                  'phone', 'liability_waiver', 'photo_consent')
        if self.event.collect_housing_data:
            fields += ('housing_status',)
        return forms.models.modelform_factory(Attendee, self.form_class, fields=fields)

    def get_object(self):
        if self.kwargs.get('pk') is None:
            return None
        else:
            return self.order.attendees.get(pk=self.kwargs['pk'])

    def get_initial(self):
        initial = super(AttendeeBasicDataView, self).get_initial()
        person = self.request.user
        if self.kwargs.get('pk') is None and not self.order.attendees.filter(person=person).exists():
            initial.update({
                'given_name': person.given_name,
                'middle_name': person.middle_name,
                'surname': person.surname,
                'name_order': person.name_order,
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
        context['attendees'] = self.order.attendees.all()
        return context


class RemoveAttendeeView(OrderMixin, View):
    @method_decorator(ajax_required)
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        Attendee.objects.filter(order=self.order,
                                pk=kwargs['pk']).delete()

        return JsonResponse({'success': True})


class AttendeeHousingView(OrderMixin, TemplateView):
    template_name = 'brambling/event/attendee_housing.html'

    def get(self, request, *args, **kwargs):
        if not self.event.collect_housing_data:
            raise Http404
        self.forms = self.get_forms()
        if not self.forms:
            return HttpResponseRedirect(self.get_success_url())
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        if not self.event.collect_housing_data:
            raise Http404
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

        attendees = self.order.attendees.filter(housing_status=Attendee.NEED)
        if not attendees:
            raise Http404
        return [AttendeeHousingDataForm(prefix='form-{}-'.format(attendee.pk),
                                        instance=attendee,
                                        **kwargs)
                for attendee in attendees]

    def get_context_data(self, **kwargs):
        context = super(AttendeeHousingView, self).get_context_data(**kwargs)

        context.update({
            'event': self.event,
            'forms': self.forms,
        })
        return context


class SurveyDataView(OrderMixin, UpdateView):
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

    def get_form_class(self):
        if not self.fields:
            raise Http404
        return forms.models.modelform_factory(Order, fields=self.fields)

    def get_object(self):
        return self.order

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


class HostingView(OrderMixin, UpdateView):
    template_name = 'brambling/event/hosting.html'
    form_class = HostingForm

    def get_object(self):
        if not self.event.collect_housing_data:
            raise Http404
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

    def get_success_url(self):
        return reverse('brambling_event_order_summary',
                       kwargs={'event_slug': self.event.slug})


class OrderDetailView(OrderMixin, TemplateView):
    template_name = 'brambling/event/order_summary.html'

    def get(self, request, *args, **kwargs):
        self.summary_data = self.order.get_summary_data()
        self.balance = self.summary_data['balance']
        if self.balance > 0 or self.order.has_cart():
            self.get_forms()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.summary_data = self.order.get_summary_data()
        self.balance = self.summary_data['balance']
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

    def get_context_data(self, **kwargs):
        context = super(OrderDetailView, self).get_context_data(**kwargs)

        context.update({
            'has_cards': self.order.person.cards.exists(),
            'new_card_form': getattr(self, 'new_card_form', None),
            'choose_card_form': getattr(self, 'choose_card_form', None),
            'balance': self.balance,
            'STRIPE_PUBLISHABLE_KEY': getattr(settings,
                                              'STRIPE_PUBLISHABLE_KEY',
                                              ''),
        })
        context.update(self.summary_data)
        return context
