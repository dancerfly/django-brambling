import json

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, View

from brambling.forms.attendee import (EventPersonForm, PersonDiscountForm,
                                      CheckoutForm, OwnerFormSet)
from brambling.models import (Item, PersonItem, ItemOption, Payment,
                              PersonDiscount, Discount)
from brambling.views.utils import (get_event_or_404, get_event_nav,
                                   get_event_admin_nav, ajax_required)


class AddToCartView(View):
    @method_decorator(ajax_required)
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        event = get_event_or_404(kwargs['slug'])
        try:
            item_option = ItemOption.objects.get(item__event=event,
                                                 pk=kwargs['pk'])
        except ItemOption.DoesNotExist:
            raise Http404

        cart = request.user.get_cart(event, create=True)
        PersonItem.objects.create(
            item_option=item_option,
            cart=cart,
            buyer=request.user
        )
        return JsonResponse({'success': True})


class RemoveFromCartView(View):
    @method_decorator(ajax_required)
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        event = get_event_or_404(kwargs['slug'])
        try:
            personitem = PersonItem.objects.get(item_option__item__event=event,
                                                pk=kwargs['pk'])
        except PersonItem.DoesNotExist:
            pass
        else:
            cart = request.user.get_cart(event)

            if personitem.cart == cart:
                personitem.delete()

            if not cart.contents.exists():
                cart.delete()

        return JsonResponse({'success': True})


class PersonDiscountView(View):
    @method_decorator(ajax_required)
    @method_decorator(login_required)
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

        event = get_event_or_404(self.kwargs['slug'])
        now = timezone.now()
        items = event.items.filter(
            options__available_start__lte=now,
            options__available_end__gte=now,
            category__in=self.categories,
        ).select_related('options').distinct()

        context.update({
            'event': event,
            'items': items,
            'discount_form': PersonDiscountForm(event=event,
                                                person=self.request.user,
                                                prefix='discount-form'),
            'cart': self.request.user.get_cart(event),
            'discounts': self.request.user.get_discounts(event),
            'event_nav': get_event_nav(event, self.request),
            'event_admin_nav': get_event_admin_nav(event, self.request),
        })
        return context


class FinalizeCartView(TemplateView):
    template_name = 'brambling/event/finalize_cart.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(FinalizeCartView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.event = get_event_or_404(kwargs['slug'])
        self.formset = self.get_formset()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.event = get_event_or_404(kwargs['slug'])
        self.formset = self.get_formset()
        if self.formset.is_valid():
            # Force saving on all the forms.
            for form in self.formset.forms:
                form.save()
            cart = request.user.get_cart(self.event)
            cart.owners_set = True
            cart.save()
            go_to_forms = False
            for personitem in cart.contents.all():
                if (personitem.item_option.item.category == Item.PASS and
                        self.event.collect_housing_data):
                    go_to_forms = True
                else:
                    personitem.is_complete = True
                    personitem.save()
            if go_to_forms:
                url = reverse('brambling_event_finalize_forms',
                              kwargs={'slug': self.event.slug})
            else:
                url = ''
            return HttpResponseRedirect(url)
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_formset(self):
        cart = self.request.user.get_cart(self.event)

        if cart is None:
            raise Http404

        qs = cart.contents.all()
        kwargs = {
            'queryset': qs,
            'default_owner': self.request.user,
        }
        if self.request.method == 'POST':
            kwargs['data'] = self.request.POST
        return OwnerFormSet(**kwargs)

    def get_context_data(self, **kwargs):
        context = super(FinalizeCartView, self).get_context_data(**kwargs)

        context.update({
            'event': self.event,
            'cart': self.request.user.get_cart(self.event),
            'formset': self.formset,
            'discount_form': PersonDiscountForm(event=self.event,
                                                person=self.request.user,
                                                prefix='discount-form'),
            'discounts': self.request.user.get_discounts(self.event),
            'event_nav': get_event_nav(self.event, self.request),
            'event_admin_nav': get_event_admin_nav(self.event, self.request),
        })
        return context


class CartFormsView(TemplateView):
    template_name = 'brambling/event/cart_forms.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(CartFormsView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.event = get_event_or_404(kwargs['slug'])
        self.forms = self.get_forms()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.event = get_event_or_404(kwargs['slug'])
        self.forms = self.get_forms()
        all_valid = True
        for form in self.forms:
            if not form.is_valid():
                all_valid = False
        if all_valid:
            for form in self.forms:
                form.save()
            cart = request.user.get_cart(self.event)
            if not cart.is_finalized():
                raise Exception("Cart is not finalized when it should be.")
            return HttpResponseRedirect(reverse('brambling_event_checkout',
                                        kwargs={'slug': self.event.slug}))
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_forms(self):
        cart = self.request.user.get_cart(self.event)
        if cart is None:
            raise Http404
        # One form for each PersonItem in the cart. Owner is fixed
        # at this point.
        memo_dict = {}
        kwargs = {
            'event': self.event,
            'memo_dict': memo_dict,
        }
        if self.request.method == 'POST':
            kwargs['data'] = self.request.POST
        return [EventPersonForm(personitem, prefix=str(personitem.pk), **kwargs)
                for personitem in cart.contents.all()]

    def get_context_data(self, **kwargs):
        context = super(CartFormsView, self).get_context_data(**kwargs)

        context.update({
            'event': self.event,
            'cart': self.request.user.get_cart(self.event),
            'forms': self.forms,
            'discount_form': PersonDiscountForm(event=self.event,
                                                person=self.request.user,
                                                prefix='discount-form'),
            'discounts': self.request.user.get_discounts(self.event),
            'event_nav': get_event_nav(self.event, self.request),
            'event_admin_nav': get_event_admin_nav(self.event, self.request),
        })
        return context


class CheckoutView(TemplateView):
    template_name = 'brambling/event/checkout.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(CheckoutView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.event = get_event_or_404(kwargs['slug'])
        self.balance = self.get_balance()
        cart = request.user.get_cart(self.event)
        if self.balance > 0 or cart is not None:
            self.form = self.get_form()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.event = get_event_or_404(kwargs['slug'])
        self.balance = self.get_balance()
        cart = request.user.get_cart(self.event)
        if self.balance > 0 or cart is not None:
            self.form = self.get_form()
            if self.form.is_valid():
                self.form.save()
                # Remove items from cart and delete it.
                cart = request.user.get_cart(self.event)
                if cart is not None:
                    cart.contents.all().update(cart=None, status=PersonItem.PAID)
                    cart.delete()
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
            event=self.event,
            person=self.request.user
        ).order_by('timestamp')
        self.personitems = PersonItem.objects.filter(
            buyer=self.request.user,
            item_option__item__event=self.event
        ).order_by('added')

        self.discounts = PersonDiscount.objects.filter(
            person=self.request.user,
            discount__event=self.event
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
        context = super(CheckoutView, self).get_context_data(**kwargs)

        context.update({
            'event': self.event,
            'cart': self.request.user.get_cart(self.event),
            'discounts': self.request.user.get_discounts(self.event),
            'discount_form': PersonDiscountForm(event=self.event,
                                                person=self.request.user,
                                                prefix='discount-form'),
            'form': getattr(self, 'form', None),
            'personitems': self.personitems,
            'payments': self.payments,
            'discounts': self.discounts,
            'total_cost': self.total_cost,
            'total_savings': self.total_savings,
            'total_payments': self.total_payments,
            'balance': self.balance,
            'event_nav': get_event_nav(self.event, self.request),
            'event_admin_nav': get_event_admin_nav(self.event, self.request),
        })
        return context
