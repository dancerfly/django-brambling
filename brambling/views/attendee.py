from datetime import timedelta
import json

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, View
from zenaida.forms import modelformset_factory

from brambling.forms.attendee import (ReservationForm, PersonItemForm,
                                      PersonItemFormSet, PersonDiscountForm,
                                      CheckoutForm)
from brambling.models import Item, PersonItem
from brambling.views.utils import (get_event_or_404, get_event_nav,
                                   get_event_admin_nav)


class ReservationView(TemplateView):
    categories = (
        Item.MERCHANDISE,
        Item.COMPETITION,
        Item.CLASS,
        Item.PASS
    )
    template_name = 'brambling/event/reserve.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ReservationView, self).dispatch(*args, **kwargs)

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

        context.update({
            'event': self.event,
            'items': items,
            'discount_form': PersonDiscountForm(event=self.event,
                                                person=self.request.user,
                                                prefix='discount-form'),
            'cart': self.request.user.get_cart(self.event),
            'cart_total': self.request.user.get_cart_total(self.event),
            'discounts': self.request.user.get_discounts(self.event),
            'event_nav': get_event_nav(self.event, self.request),
            'event_admin_nav': get_event_admin_nav(self.event, self.request),
        })
        return context

    def get(self, request, *args, **kwargs):
        self.event = get_event_or_404(kwargs['slug'])
        self.items = self.get_items()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.event = get_event_or_404(kwargs['slug'])
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

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(CartView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.event = get_event_or_404(kwargs['slug'])
        self.formset = self.get_formset()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.event = get_event_or_404(kwargs['slug'])
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
        formset_class = modelformset_factory(PersonItem,
                                             PersonItemForm,
                                             formset=PersonItemFormSet,
                                             extra=0)

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
            'discount_form': PersonDiscountForm(event=self.event,
                                                person=self.request.user,
                                                prefix='discount-form'),
            'discounts': self.request.user.get_discounts(self.event),
            'event_nav': get_event_nav(self.event, self.request),
            'event_admin_nav': get_event_admin_nav(self.event, self.request),
        })
        context['formset'].forms
        return context


class CheckoutView(TemplateView):
    template_name = 'brambling/event/checkout.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(CheckoutView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.event = get_event_or_404(kwargs['slug'])
        self.form = self.get_form()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_form(self):
        kwargs = {
            'person': self.request.user,
            'event': self.event,
        }
        if self.request.method == 'POST':
            kwargs['data'] = self.request.POST
        return CheckoutForm(**kwargs)

    def post(self, request, *args, **kwargs):
        self.event = get_event_or_404(kwargs['slug'])
        self.form = self.get_form()
        if self.form.is_valid():
            self.form.save()
            return HttpResponseRedirect('')
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super(CheckoutView, self).get_context_data(**kwargs)

        checkout_list = [(payment.timestamp, payment)
                         for payment in self.form.payments]
        checkout_list += [(item.added, item)
                          for item in self.form.personitems]
        checkout_list.sort()

        context.update({
            'event': self.event,
            'cart_total': self.request.user.get_cart_total(self.event),
            'discounts': self.request.user.get_discounts(self.event),
            'discount_form': PersonDiscountForm(event=self.event,
                                                person=self.request.user,
                                                prefix='discount-form'),
            'form': self.form,
            'checkout_list': checkout_list,
            'balance': self.form.balance,
            'event_nav': get_event_nav(self.event, self.request),
            'event_admin_nav': get_event_admin_nav(self.event, self.request),
        })
        return context


class PersonDiscountView(View):
    def post(self, request, *args, **kwargs):
        if not request.is_ajax():
            raise Http404

        event = get_event_or_404(kwargs['slug'])

        form = PersonDiscountForm(
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
