from django.conf import settings
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import reverse
from django.db.models import Count, Q
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView, View, UpdateView
import floppyforms.__future__ as forms

from brambling.forms.orders import (SavedCardPaymentForm, OneTimePaymentForm,
                                    HostingForm, AttendeeBasicDataForm,
                                    AttendeeHousingDataForm, DwollaPaymentForm,
                                    SurveyDataForm, CheckPaymentForm)
from brambling.mail import OrderReceiptMailer, OrderAlertMailer
from brambling.models import (Item, BoughtItem, ItemOption,
                              BoughtItemDiscount, Discount, Order,
                              Attendee, EventHousing, Event, Transaction)
from brambling.utils.payment import dwolla_customer_oauth_url
from brambling.views.utils import (get_event_admin_nav, ajax_required,
                                   clear_expired_carts, Workflow, Step,
                                   WorkflowMixin)


ORDER_CODE_SESSION_KEY = '_brambling_order_code'
ORDER_CODE_ALLOWED_CHARS = 'abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'


class RactiveShopView(TemplateView):
    template_name = 'brambling/event/order/register.html'

    def get_context_data(self, **kwargs):
        context = super(RactiveShopView, self).get_context_data(**kwargs)
        event = get_object_or_404(Event.objects.select_related('organization'),
                                  slug=kwargs['event_slug'],
                                  organization__slug=kwargs['organization_slug'])

        editable_by_user = event.editable_by(self.request.user)

        if not event.is_published and not editable_by_user:
            raise Http404

        clear_expired_carts(event)
        context['event'] = event
        context['editable_by_user'] = editable_by_user
        return context


class OrderStep(Step):
    view_name = None

    @property
    def url(self):
        kwargs = {
            'event_slug': self.workflow.event.slug,
            'organization_slug': self.event.organization.slug,
        }
        if self.workflow.order.person_id is None:
            kwargs['code'] = self.workflow.order.code
        return reverse(self.view_name, kwargs=kwargs)


class ShopStep(OrderStep):
    name = 'Shop'
    slug = 'shop'
    view_name = 'brambling_event_shop'

    def _is_completed(self):
        order = self.workflow.order
        if not order:
            return False
        return order.cart_start_time is not None or order.bought_items.exists()


class AttendeeStep(OrderStep):
    name = 'Attendees'
    slug = 'attendees'
    view_name = 'brambling_event_attendee_list'

    def _is_completed(self):
        if not self.workflow.order:
            return False
        return not self.workflow.order.bought_items.filter(attendee__isnull=True).exclude(status=BoughtItem.REFUNDED).exists()

    def get_errors(self):
        errors = []
        order = self.workflow.order
        # All attendees must have at least one non-refunded item
        total_count = order.attendees.count()
        valid_statuses = (BoughtItem.RESERVED, BoughtItem.UNPAID, BoughtItem.BOUGHT)
        with_count = order.attendees.filter(bought_items__status__in=valid_statuses).distinct().count()
        if with_count != total_count:
            errors.append('All attendees must have at least one item')

        # All attendees must have basic data filled out.
        missing_data = order.attendees.filter(basic_completed=False)
        if len(missing_data) > 0:
            if len(missing_data) == 1:
                error = '{} is missing basic data'.format(missing_data[0])
            else:
                error = 'The following attendees are missing basic data: ' + ", ".join(missing_data)
            errors.append(error)

        # All items must be assigned to an attendee.
        if order.bought_items.filter(attendee__isnull=True).exclude(status=BoughtItem.REFUNDED).exists():
            errors.append('All items in order must be assigned to an attendee.')
        return errors


class HousingStep(OrderStep):
    name = 'Housing'
    slug = 'housing'
    view_name = 'brambling_event_attendee_housing'

    @classmethod
    def include_in(cls, workflow):
        return workflow.event.collect_housing_data

    def is_active(self):
        if not self.workflow.order:
            return False
        if not hasattr(self, '_active'):
            self._active = self.workflow.order.attendees.filter(housing_status=Attendee.NEED).exists()
        return self._active

    def _is_completed(self):
        if not self.workflow.order:
            return False
        return not self.workflow.order.attendees.filter(
            housing_status=Attendee.NEED,
            housing_completed=False
        ).exists()

    def get_errors(self):
        errors = []
        order = self.workflow.order

        missing_housing = order.attendees.filter(housing_status=Attendee.NEED,
                                                 housing_completed=False).exists()
        if missing_housing:
            errors.append("Some attendees are missing housing data.")
        return errors


class SurveyStep(OrderStep):
    name = 'Survey'
    slug = 'survey'
    view_name = 'brambling_event_survey'

    @classmethod
    def include_in(cls, workflow):
        return workflow.event.collect_survey_data

    def _is_completed(self):
        if not self.workflow.order:
            return False
        return self.workflow.order.survey_completed


class HostingStep(OrderStep):
    name = 'Hosting'
    slug = 'hosting'
    view_name = 'brambling_event_hosting'

    @classmethod
    def include_in(cls, workflow):
        return workflow.event.collect_housing_data

    def is_active(self):
        if not self.workflow.order:
            return False
        if not hasattr(self, '_active'):
            self._active = self.workflow.order.attendees.exclude(housing_status=Attendee.NEED).exists()
        return self._active

    def _is_completed(self):
        if not self.workflow.order:
            return False
        return (not self.workflow.order.providing_housing) or EventHousing.objects.filter(
            event=self.workflow.event,
            order=self.workflow.order
        ).exists()


class OrderEmailStep(OrderStep):
    name = 'Email'
    slug = 'email'
    view_name = 'brambling_event_order_email'

    @classmethod
    def include_in(cls, workflow):
        return workflow.order is None or workflow.order.person is None

    def _is_completed(self):
        if not self.workflow.order:
            return False
        return bool(self.workflow.order.email)


class PaymentStep(OrderStep):
    name = 'Payment'
    slug = 'payment'
    view_name = 'brambling_event_order_summary'

    def _is_completed(self):
        return False


class RegistrationWorkflow(Workflow):
    step_classes = [ShopStep, AttendeeStep, HousingStep, SurveyStep,
                    HostingStep, OrderEmailStep, PaymentStep]


class ShopWorkflow(Workflow):
    step_classes = [ShopStep, AttendeeStep, HousingStep, HostingStep, PaymentStep]


class SurveyWorkflow(Workflow):
    step_classes = [SurveyStep, PaymentStep]


class HostingWorkflow(Workflow):
    step_classes = [HostingStep, PaymentStep]


class OrderMixin(object):
    current_step_slug = None

    def dispatch(self, request, *args, **kwargs):
        self.event = get_object_or_404(Event.objects.select_related('organization'),
                                       slug=kwargs['event_slug'],
                                       organization__slug=kwargs['organization_slug'])
        if not self.event.viewable_by(request.user):
            raise Http404

        try:
            self.order = self.get_order()
        except Order.DoesNotExist:
            raise Http404

        if self.order and self.order.cart_is_expired():
            self.order.delete_cart()
        return super(OrderMixin, self).dispatch(request, *args, **kwargs)

    def get_order(self):
        order_kwargs = {
            'event': self.event,
            'person': self.request.user if self.request.user.is_authenticated() else None,
        }
        code_in_url = False
        order = None
        session_orders = self.request.session.get(ORDER_CODE_SESSION_KEY, {})

        if self.kwargs.get('code'):
            if str(self.event.pk) in session_orders:
                del session_orders[str(self.event.pk)]
            order_kwargs['code'] = self.kwargs['code']
            code_in_url = True
        elif str(self.event.pk) in session_orders:
            order_kwargs['code'] = session_orders[str(self.event.pk)]
        try:
            if order_kwargs['person'] or order_kwargs.get('code'):
                order = Order.objects.get(**order_kwargs)
        except Order.DoesNotExist:
            # If it was in the URL, re-raise the error.
            if code_in_url:
                raise

            # Also be sure to remove the code from the session,
            # if that's what they were using.
            if order_kwargs.get('code'):
                del session_orders[str(self.event.pk)]

                # If the user is authenticated, try to get the order
                # they have for this event. Maybe the code snuck in there
                # somehow?
                if self.request.user.is_authenticated():
                    try:
                        order = Order.objects.get(
                            event=self.event,
                            person=self.request.user
                        )
                    except Order.DoesNotExist:
                        # See if the order exists and belongs to an
                        # unauthenticated user. If so, and if that user hasn't
                        # checked out yet, assume that the user created an
                        # account mid-order and re-assign it.
                        try:
                            order = Order.objects.get(
                                bought_items__status__in=[
                                    BoughtItem.RESERVED,
                                    BoughtItem.UNPAID,
                                ],
                                event=self.event,
                                person__isnull=True,
                                code=order_kwargs['code']
                            )
                        except Order.DoesNotExist:
                            pass
                        else:
                            order.person = self.request.user
                            order.save()
        return order

    def create_order(self):
        person = self.request.user if self.request.user.is_authenticated() else None
        code = get_random_string(8, ORDER_CODE_ALLOWED_CHARS)

        while Order.objects.filter(event=self.event, code=code).exists():
            code = get_random_string(8, ORDER_CODE_ALLOWED_CHARS)
        order = Order.objects.create(event=self.event, person=person, code=code)

        if not self.request.user.is_authenticated():
            session_orders = self.request.session.get(ORDER_CODE_SESSION_KEY, {})
            session_orders[str(self.event.pk)] = code
            self.request.session[ORDER_CODE_SESSION_KEY] = session_orders
        return order

    def get_context_data(self, **kwargs):
        context = super(OrderMixin, self).get_context_data(**kwargs)
        context.update({
            'event': self.event,
            'order': self.order,
            # Use codes if a code was used and there's no authenticated user.
            'code_in_url': (True if self.kwargs.get('code') and
                            not self.request.user.is_authenticated() else False),
            'event_admin_nav': get_event_admin_nav(self.event, self.request),
            'site': get_current_site(self.request),
            'workflow': self.workflow,
            'current_step': self.current_step,
            'next_step': self.current_step.next_step if self.current_step else None,
        })
        return context

    def get_workflow_kwargs(self):
        # Only used if this is combined with WorkflowMixin.
        return {
            'event': self.event,
            'order': self.order
        }

    def get_reverse_kwargs(self):
        # Only used if this is combined with WorkflowMixin.
        kwargs = {
            'event_slug': self.event.slug,
            'organization_slug': self.event.organization.slug,
        }
        if self.kwargs.get('code'):
            kwargs['code'] = self.order.code
        return kwargs


class AddToOrderView(OrderMixin, View):
    @method_decorator(ajax_required)
    def post(self, request, *args, **kwargs):
        clear_expired_carts(self.event)

        try:
            item_option = ItemOption.objects.get(item__event=self.event,
                                                 pk=kwargs['pk'])
        except ItemOption.DoesNotExist:
            raise Http404

        # If a total number is set and has been reached, the item is sold out.
        if item_option.total_number is not None and item_option.remaining <= 0:
            return JsonResponse({'success': False, 'error': 'That item is sold out.'})

        self.order.add_to_cart(item_option)
        return JsonResponse({'success': True})

    def get_order(self):
        order = super(AddToOrderView, self).get_order()

        if order is None:
            order = self.create_order()
        return order


class RemoveFromOrderView(View):
    @method_decorator(ajax_required)
    def post(self, request, *args, **kwargs):
        try:
            bought_item = BoughtItem.objects.get(pk=kwargs['pk'])
        except BoughtItem.DoesNotExist:
            return JsonResponse({'success': True})

        if ((request.user.is_authenticated() and not bought_item.order.person == request.user) or
                (not request.user.is_authenticated() and bought_item.order.person is not None)):
            return JsonResponse({'error': "You do not own that item."}, status=403)

        bought_item.order.remove_from_cart(bought_item)

        return JsonResponse({'success': True})


class ApplyDiscountView(OrderMixin, View):
    @method_decorator(ajax_required)
    def post(self, request, *args, **kwargs):
        discounts = Discount.objects.filter(
            code=kwargs['discount'],
            event=self.event
        )
        now = timezone.now()
        try:
            discount = discounts.filter(
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

        created = self.order.add_discount(discount, force=False)
        if created:
            return JsonResponse({
                'success': True,
                'name': discount.name,
                'code': discount.code,
            })
        return JsonResponse({
            'success': True,
        })

    def get_order(self):
        order = super(ApplyDiscountView, self).get_order()

        if order is None:
            order = self.create_order()
        return order


class ChooseItemsView(OrderMixin, WorkflowMixin, TemplateView):
    template_name = 'brambling/event/order/shop.html'
    current_step_slug = 'shop'
    workflow_class = RegistrationWorkflow

    @method_decorator(ensure_csrf_cookie)
    def dispatch(self, *args, **kwargs):
        return super(ChooseItemsView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ChooseItemsView, self).get_context_data(**kwargs)
        clear_expired_carts(self.event)
        now = timezone.now()
        item_options = ItemOption.objects.filter(
            available_start__lte=now,
            available_end__gte=now,
            item__event=self.event,
        ).order_by('item', 'order').extra(select={
            'taken': """
SELECT COUNT(*) FROM brambling_boughtitem WHERE
brambling_boughtitem.item_option_id = brambling_itemoption.id AND
brambling_boughtitem.status != 'refunded'
"""
        })

        context['item_options'] = item_options
        if self.order is not None:
            context['discounts'] = Discount.objects.filter(
                orderdiscount__order=self.order).distinct()
        return context


class AttendeesView(OrderMixin, WorkflowMixin, TemplateView):
    template_name = 'brambling/event/order/attendees.html'
    current_step_slug = 'attendees'
    workflow_class = RegistrationWorkflow

    def get(self, request, *args, **kwargs):
        self.attendees = self.order.attendees.all()
        if self.attendees:
            return self.render_to_response(self.get_context_data())

        kwargs = {
            'event_slug': self.event.slug,
            'organization_slug': self.event.organization.slug,
        }
        if self.kwargs.get('code') and not self.request.user.is_authenticated():
            kwargs['code'] = self.order.code
        return HttpResponseRedirect(reverse('brambling_event_attendee_add',
                                            kwargs=kwargs))

    def get_context_data(self, **kwargs):
        context = super(AttendeesView, self).get_context_data(**kwargs)

        context.update({
            'errors': self.current_step.errors,
            'attendees': self.attendees,
            'unassigned_items': self.order.bought_items.filter(
                attendee__isnull=True
            ).exclude(
                status=BoughtItem.REFUNDED
            ).order_by('item_option__item', 'item_option'),
        })
        return context


class AttendeeBasicDataView(OrderMixin, WorkflowMixin, UpdateView):
    template_name = 'brambling/event/order/attendee_basic_data.html'
    form_class = AttendeeBasicDataForm
    current_step_slug = 'attendees'
    workflow_class = RegistrationWorkflow
    model = Attendee

    def get_object(self):
        if 'pk' not in self.kwargs:
            return None
        return super(AttendeeBasicDataView, self).get_object()

    def get_form_class(self):
        fields = ('given_name', 'middle_name', 'surname', 'name_order', 'email',
                  'phone', 'liability_waiver', 'photo_consent')
        if self.event.collect_housing_data:
            fields += ('housing_status',)
        return forms.models.modelform_factory(Attendee, self.form_class, fields=fields)

    def get_initial(self):
        initial = super(AttendeeBasicDataView, self).get_initial()
        if self.order.attendees.count() == 0 and self.request.user.is_authenticated():
            person = self.request.user
            initial.update({
                'given_name': person.given_name,
                'middle_name': person.middle_name,
                'surname': person.surname,
                'name_order': person.name_order,
                'email': person.email,
                'phone': person.phone
            })
        return initial

    def get_form_kwargs(self):
        kwargs = super(AttendeeBasicDataView, self).get_form_kwargs()
        kwargs['order'] = self.order
        return kwargs

    def form_valid(self, form):
        if (self.request.user.is_authenticated() and
                form.instance.email == self.request.user.email):
            form.instance.person = self.request.user
            form.instance.person_confirmed = True

        self.object = form.save()
        return super(AttendeeBasicDataView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(AttendeeBasicDataView, self).get_context_data(**kwargs)
        context.update({
            'attendees': Attendee.objects.filter(order=self.order).order_by('pk')
        })
        return context


class AttendeeHousingView(OrderMixin, WorkflowMixin, TemplateView):
    template_name = 'brambling/event/order/attendee_housing.html'
    current_step_slug = 'housing'
    workflow_class = RegistrationWorkflow

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
        kwargs = {
            'event_slug': self.event.slug,
            'organization_slug': self.event.organization.slug,
        }
        if self.kwargs.get('code') and not self.request.user.is_authenticated():
            kwargs['code'] = self.order.code
        return reverse('brambling_event_survey', kwargs=kwargs)

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


class SurveyDataView(OrderMixin, WorkflowMixin, UpdateView):
    template_name = 'brambling/event/order/survey.html'
    context_object_name = 'order'
    current_step_slug = 'survey'
    form_class = SurveyDataForm
    workflow_class = RegistrationWorkflow

    def get_object(self):
        return self.order

    def form_valid(self, form):
        self.object.survey_completed = True
        form.save()
        return super(SurveyDataView, self).form_valid(form)


class HostingView(OrderMixin, WorkflowMixin, UpdateView):
    template_name = 'brambling/event/order/hosting.html'
    form_class = HostingForm
    current_step_slug = 'hosting'
    workflow_class = RegistrationWorkflow

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
                home=self.order.person.home if self.order.person_id is not None else None
            )

    def get_success_url(self):
        kwargs = {
            'event_slug': self.event.slug,
            'organization_slug': self.event.organization.slug,
        }
        if self.kwargs.get('code') and not self.request.user.is_authenticated():
            kwargs['code'] = self.order.code
        return reverse('brambling_event_order_summary', kwargs=kwargs)


class OrderEmailView(OrderMixin, WorkflowMixin, UpdateView):
    template_name = 'brambling/event/order/email.html'
    current_step_slug = 'email'
    workflow_class = RegistrationWorkflow

    def get_form_class(self):
        cls = forms.models.modelform_factory(Order, forms.ModelForm, fields=('email',))
        cls.base_fields['email'].required = True
        return cls

    def get_object(self):
        return self.order


class SummaryView(OrderMixin, WorkflowMixin, TemplateView):
    template_name = 'brambling/event/order/summary.html'
    current_step_slug = 'payment'
    workflow_class = RegistrationWorkflow

    def get(self, request, *args, **kwargs):
        self.summary_data = self.order.get_summary_data()
        self.net_balance = self.summary_data['net_balance']
        if self.net_balance > 0 or self.order.has_cart():
            self.get_forms()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.summary_data = self.order.get_summary_data()
        self.net_balance = self.summary_data['net_balance']
        if self.net_balance == 0:
            valid = True
            payment = Transaction.objects.create(
                amount=0,
                method=Transaction.FAKE,
                transaction_type=Transaction.PURCHASE,
                is_confirmed=True,
                api_type=self.event.api_type,
                event=self.event,
                order=self.order,
            )
            self.order.mark_cart_paid(payment)
        else:
            self.get_forms()
            form = None
            valid = False
            if 'choose_card' in request.POST:
                # Get a choose form.
                form = self.choose_card_form
            if 'new_card' in request.POST:
                # Get a new form.
                form = self.new_card_form
            if 'dwolla' in request.POST:
                form = self.dwolla_form
            if 'check' in request.POST:
                form = self.check_form
            if form and form.is_valid():
                valid = True
                payment = form.save()
                self.order.mark_cart_paid(payment)
                if not self.event.is_frozen:
                    self.event.is_frozen = True
                    self.event.save()
                summary_data = self.order.get_summary_data()
                email_kwargs = {
                    'order': self.order,
                    'summary_data': summary_data,
                    'site': get_current_site(self.request),
                    'secure': self.request.is_secure()
                }
                OrderReceiptMailer(**email_kwargs).send()
                OrderAlertMailer(**email_kwargs).send()

                session_orders = self.request.session.get(ORDER_CODE_SESSION_KEY, {})
                if str(self.event.pk) in session_orders:
                    del session_orders[str(self.event.pk)]
                    self.request.session[ORDER_CODE_SESSION_KEY] = session_orders
            elif form:
                for error in form.non_field_errors():
                    messages.error(request, error)

        if valid:
            if not self.order.person:
                url = reverse('brambling_event_order_summary', kwargs={
                    'event_slug': self.event.slug,
                    'organization_slug': self.event.organization.slug,
                    'code': self.order.code
                })
                return HttpResponseRedirect(url)
            return HttpResponseRedirect('')
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_forms(self):
        kwargs = {
            'order': self.order,
            'amount': self.net_balance,
        }
        choose_data = None
        new_data = None
        dwolla_data = None
        check_data = None
        if self.request.method == 'POST':
            if 'choose_card' in self.request.POST and self.event.stripe_connected():
                choose_data = self.request.POST
            elif 'new_card' in self.request.POST and self.event.stripe_connected():
                new_data = self.request.POST
            elif 'dwolla' in self.request.POST and self.event.dwolla_connected():
                dwolla_data = self.request.POST
            elif 'check' in self.request.POST and self.event.organization.check_payment_allowed:
                check_data = self.request.POST
        if self.event.stripe_connected():
            if self.order.person_id is not None:
                self.choose_card_form = SavedCardPaymentForm(data=choose_data, **kwargs)
            else:
                self.choose_card_form = None
            self.new_card_form = OneTimePaymentForm(data=new_data, user=self.request.user, **kwargs)
        if self.event.dwolla_connected():
            self.dwolla_form = DwollaPaymentForm(data=dwolla_data, user=self.request.user, **kwargs)
        if self.event.organization.check_payment_allowed:
            self.check_form = CheckPaymentForm(data=check_data, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SummaryView, self).get_context_data(**kwargs)

        context.update({
            'attendees': self.order.attendees.all(),
            'new_card_form': getattr(self, 'new_card_form', None),
            'choose_card_form': getattr(self, 'choose_card_form', None),
            'dwolla_form': getattr(self, 'dwolla_form', None),
            'check_form': getattr(self, 'check_form', None),
            'net_balance': self.net_balance,
            'STRIPE_PUBLISHABLE_KEY': getattr(settings,
                                              'STRIPE_PUBLISHABLE_KEY',
                                              ''),
            'STRIPE_TEST_PUBLISHABLE_KEY': getattr(settings,
                                                   'STRIPE_TEST_PUBLISHABLE_KEY',
                                                   ''),
        })
        user = self.request.user
        dwolla_obj = user if user.is_authenticated() else self.order
        dwolla_connected = dwolla_obj.dwolla_live_connected() if self.event.api_type == Event.LIVE else dwolla_obj.dwolla_test_connected()
        dwolla_can_connect = dwolla_obj.dwolla_live_can_connect() if self.event.api_type == Event.LIVE else dwolla_obj.dwolla_test_can_connect()
        if dwolla_can_connect:
            kwargs = {
                'event_slug': self.event.slug,
                'organization_slug': self.event.organization.slug,
            }
            if self.kwargs.get('code') and not self.request.user.is_authenticated():
                kwargs['code'] = self.order.code
            next_url = reverse('brambling_event_order_summary', kwargs=kwargs)
            context['dwolla_oauth_url'] = dwolla_customer_oauth_url(
                dwolla_obj, self.event.api_type, self.request, next_url)
        if dwolla_connected:
            context.update({
                'dwolla_is_connected': True,
                'dwolla_user_id': dwolla_obj.dwolla_user_id if self.event.api_type == Event.LIVE else dwolla_obj.dwolla_test_user_id
            })
        context.update(self.summary_data)
        return context
