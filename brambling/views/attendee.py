import json

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, View

from brambling.forms.attendee import (EventPersonForm, PersonDiscountForm,
                                      CheckoutForm, OwnerFormSet,
                                      HousingRequestForm, EventHousingForm)
from brambling.models import (Item, PersonItem, ItemOption, Payment,
                              PersonDiscount, Discount, EventPerson,
                              HousingRequest, EventHousing)
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


# Registration works like this:
# 1. Shop. Choose things.
# 2. Who are these for? <- part of shop?
# 3. Any relevant EventPerson fields <- Registration information. one page per pass.
# 4. If housing is enabled, one page per pass that requests or offers housing.
# 5. Checkout - unpaid items only. List any applicable credits without explanation.


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


class OwnershipView(TemplateView):
    template_name = 'brambling/event/ownership.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.event = get_event_or_404(kwargs['slug'])
        cart = request.user.get_cart(self.event)
        if cart is None:
            return HttpResponseRedirect(reverse('brambling_event_shop',
                                                kwargs={'slug': self.event.slug}))
        return super(OwnershipView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        cart = self.request.user.get_cart(self.event)
        # Count of passes being bought.
        cart_pass_count = len([pi for pi in cart.contents.all()
                               if pi.item_option.item.category == Item.PASS])

        # Whether user is already owner of a paid-for pass.
        # People can only own one pass.
        buyer_has_pass = PersonItem.objects.filter(
            status__in=(PersonItem.PAID, PersonItem.PARTIAL),
            owner=self.request.user,
            item_option__item__event=self.event
        ).exists()

        if cart_pass_count == 0 or (cart_pass_count == 1 and not buyer_has_pass):
            # Assume everything belongs to the buyer and skip to the next step.
            cart.contents.update(owner=request.user)
            cart.owners_set = True
            cart.save()
            return HttpResponseRedirect(self.get_success_url())
        self.formset = self.get_formset()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.formset = self.get_formset()
        if self.formset.is_valid():
            # Force saving on all the forms.
            for form in self.formset.forms:
                form.save()
            cart = request.user.get_cart(self.event)
            cart.owners_set = True
            cart.save()
            return HttpResponseRedirect(self.get_success_url())
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_success_url(self):
        cart = self.request.user.get_cart(self.event)

        # If they have any passes in their cart, send them to
        # fill out pass data.
        for item in cart.contents.all():
            if item.item_option.item.category == Item.PASS:
                return reverse('brambling_event_registration_data',
                               kwargs={'slug': self.event.slug})
        # Otherwise, straight to checkout.
        return reverse('brambling_event_records',
                       kwargs={'slug': self.event.slug})

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
        context = super(OwnershipView, self).get_context_data(**kwargs)

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


class RegistrationDataView(TemplateView):
    template_name = 'brambling/event/registration_data.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.event = get_event_or_404(kwargs['slug'])
        cart = request.user.get_cart(self.event)
        if cart is None:
            return HttpResponseRedirect(reverse('brambling_event_shop',
                                                kwargs={'slug': self.event.slug}))
        return super(RegistrationDataView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.forms = self.get_forms()
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
        # If we're here, we know they have passes. All that matters
        # is whether the event is doing housing (and whether they've
        # asked for it/offered it)
        if self.event.collect_housing_data:
            cart = self.request.user.get_cart(self.event)
            for item in cart.contents.all():
                if (item.item_option.item.category == Item.PASS and
                        item.eventperson.status in (EventPerson.NEED, EventPerson.HOST)):
                    return reverse('brambling_event_housing_data',
                                   kwargs={'slug': self.event.slug})
        return reverse('brambling_event_records',
                       kwargs={'slug': self.event.slug})

    def get_forms(self):
        cart = self.request.user.get_cart(self.event)
        kwargs = {}
        if self.request.method == 'POST':
            kwargs['data'] = self.request.POST

        passes_with = cart.contents.filter(
            item_option__item__category=Item.PASS,
            eventperson__isnull=False
        ).select_related('eventperson')
        passes_without = cart.contents.filter(
            item_option__item__category=Item.PASS,
            eventperson__isnull=True
        ).select_related('owner')

        forms = []
        for personitem in passes_with:
            instance = personitem.eventperson
            forms.append(EventPersonForm(instance=instance,
                                         prefix=str(personitem.pk),
                                         **kwargs))

        for personitem in passes_without:
            instance = EventPerson(event=self.event,
                                   person=personitem.owner,
                                   event_pass=personitem)
            forms.append(EventPersonForm(instance=instance,
                                         prefix=str(personitem.pk),
                                         **kwargs))
        return forms

    def get_context_data(self, **kwargs):
        context = super(RegistrationDataView, self).get_context_data(**kwargs)

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


class HousingDataView(TemplateView):
    template_name = 'brambling/event/housing_data.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.event = get_event_or_404(kwargs['slug'])
        if not self.event.collect_housing_data:
            raise Http404("Event doesn't collect housing data.")
        cart = request.user.get_cart(self.event)
        if cart is None:
            return HttpResponseRedirect(reverse('brambling_event_shop',
                                                kwargs={'slug': self.event.slug}))
        return super(HousingDataView, self).dispatch(request, *args, **kwargs)

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
        return reverse('brambling_event_records',
                       kwargs={'slug': self.event.slug})

    def get_forms(self):
        cart = self.request.user.get_cart(self.event)

        # One form for each EventPerson attached to the cart which is either
        # requesting or offering housing. Owner is fixed at this point - as is
        # housing status.
        memo_dict = {}
        kwargs = {
            'memo_dict': memo_dict,
            'request': self.request,
        }
        if self.request.method == 'POST':
            kwargs['data'] = self.request.POST

        eventpeople = EventPerson.objects.filter(event_pass__cart=cart,
                                                 status__in=(EventPerson.NEED,
                                                             EventPerson.HOST)
                                                 ).select_related('person', 'event')
        forms = []
        for eventperson in eventpeople:
            if eventperson.status == EventPerson.NEED:
                form_class = HousingRequestForm
                instance_kwargs = {
                    'event': eventperson.event,
                    'person': eventperson.person,
                }
                try:
                    instance = HousingRequest.objects.get(**instance_kwargs)
                except HousingRequest.DoesNotExist:
                    instance = HousingRequest(**instance_kwargs)
            else:
                form_class = EventHousingForm
                instance_kwargs = {
                    'event': eventperson.event,
                    'home': eventperson.person.home,
                }
                try:
                    instance = EventHousing.objects.get(**instance_kwargs)
                except EventHousing.DoesNotExist:
                    instance = EventHousing(**instance_kwargs)
            forms.append(form_class(instance=instance,
                                    eventperson=eventperson,
                                    prefix=str(eventperson.pk),
                                    **kwargs))
        return forms

    def get_context_data(self, **kwargs):
        context = super(HousingDataView, self).get_context_data(**kwargs)

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


class RecordsView(TemplateView):
    template_name = 'brambling/event/records.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(RecordsView, self).dispatch(*args, **kwargs)

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
        context = super(RecordsView, self).get_context_data(**kwargs)

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
