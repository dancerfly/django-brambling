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
                                   clear_expired_carts, Workflow, Step)


class ShopStep(Step):
    name = 'Shop'
    slug = 'shop'

    @property
    def url(self):
        return reverse('brambling_event_shop',
                       kwargs={'event_slug': self.workflow.event.slug})

    def _is_completed(self):
        return self.workflow.order.has_cart()


class AttendeeStep(Step):
    name = 'Attendees'
    slug = 'attendees'

    @property
    def url(self):
        return reverse('brambling_event_attendee_list',
                       kwargs={'event_slug': self.workflow.event.slug})

    def _is_completed(self):
        return not self.workflow.order.bought_items.filter(attendee__isnull=True).exists()

    def get_errors(self):
        errors = []
        order = self.workflow.order
        # All attendees must have at least one class or pass
        total_count = order.attendees.count()
        with_count = order.attendees.filter(bought_items__item_option__item__category=Item.PASS).count()
        if with_count != total_count:
            errors.append('All attendees must have exactly one pass')

        # Attendees may not have more than one pass.
        attendees = order.attendees.filter(
            bought_items__item_option__item__category=Item.PASS
        ).distinct().annotate(
            Count('bought_items')
        ).filter(
            bought_items__count__gte=2
        )
        if len(attendees) > 0:
            if len(attendees) == 1:
                error = '{} has too many passes (more than one).'.format(attendees[0])
            else:
                error = 'The following attendees have too many passes (more than one): ' + ", ".join(attendees)
            errors.append(error)

        # All attendees must have basic data filled out.
        missing_data = order.attendees.filter(basic_completed=False)
        if len(missing_data) > 0:
            if len(missing_data) == 1:
                error = '{} is missing basic data'.format(missing_data[0])
            else:
                error = 'The following attendees are missing basic data: ' + ", ".join(missing_data)
            errors.append(error)

        # All items must be assigned to an attendee.
        if order.bought_items.filter(attendee__isnull=True).exists():
            errors.append('All items in order must be assigned to an attendee.')
        return errors


class HousingStep(Step):
    name = 'Housing'
    slug = 'housing'

    @classmethod
    def include_in(cls, workflow):
        return workflow.event.collect_housing_data

    @property
    def url(self):
        return reverse('brambling_event_attendee_housing',
                       kwargs={'event_slug': self.workflow.event.slug})

    def is_active(self):
        return self.workflow.order.attendees.filter(
            housing_status=Attendee.NEED).exists()

    def _is_completed(self):
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


class SurveyStep(Step):
    name = 'Survey'
    slug = 'survey'

    @classmethod
    def include_in(cls, workflow):
        return (workflow.event.collect_housing_data or
                workflow.event.collect_survey_data)

    @property
    def url(self):
        return reverse('brambling_event_survey',
                       kwargs={'event_slug': self.workflow.event.slug})

    def _is_completed(self):
        return self.workflow.order.survey_completed


class HostingStep(Step):
    name = 'Hosting'
    slug = 'hosting'

    @classmethod
    def include_in(cls, workflow):
        return workflow.event.collect_housing_data

    @property
    def url(self):
        return reverse('brambling_event_hosting',
                       kwargs={'event_slug': self.workflow.event.slug})

    def is_active(self):
        return self.workflow.order.providing_housing

    def _is_completed(self):
        return EventHousing.objects.filter(
            event=self.workflow.event,
            order=self.workflow.order
        ).exists()


class PaymentStep(Step):
    name = 'Payment'
    slug = 'payment'

    @property
    def url(self):
        return reverse('brambling_event_order_summary',
                       kwargs={'event_slug': self.workflow.event.slug})

    def _is_completed(self):
        return False


class RegistrationWorkflow(Workflow):
    step_classes = [ShopStep, AttendeeStep, HousingStep, SurveyStep,
                    HostingStep, PaymentStep]


class OrderMixin(object):
    current_step_slug = None

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
        self.workflow = self.get_workflow()
        if self.workflow is None or self.current_step_slug is None:
            self.current_step = None
        else:
            self.current_step = self.workflow.steps[self.current_step_slug]
            if not self.current_step.is_active() or not self.current_step.is_accessible():
                for step in reversed(self.workflow.steps.values()):
                    if step.is_accessible() and step.is_active():
                        return HttpResponseRedirect(step.url)
        return super(OrderMixin, self).dispatch(*args, **kwargs)

    @property
    def is_admin_request(self):
        if not hasattr(self, '_is_admin_request'):
            self._is_admin_request = self.event.editable_by(self.request.user)
        return self._is_admin_request

    def get_workflow(self):
        kwargs = {
            'event': self.event,
            'order': self.order
        }
        return RegistrationWorkflow(**kwargs)

    def get_context_data(self, **kwargs):
        context = super(OrderMixin, self).get_context_data(**kwargs)
        context.update({
            'event': self.event,
            'order': self.order,
            'event_admin_nav': get_event_admin_nav(self.event, self.request),
            'is_admin_request': self.is_admin_request,
            'workflow': self.workflow,
            'current_step': self.current_step,
            'next_step': self.current_step.next_step if self.current_step else None,
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

    def get_workflow(self):
        return None


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

    def get_workflow(self):
        return None


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

        created = self.order.add_discount(discount, force=self.is_admin_request)
        if created:
            return JsonResponse({
                'success': True,
                'name': discount.name,
                'code': discount.code,
            })
        return JsonResponse({
            'success': True,
        })

    def get_workflow(self):
        return None


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

    def get_workflow(self):
        return None


class ChooseItemsView(OrderMixin, TemplateView):
    template_name = 'brambling/event/order/shop.html'
    current_step_slug = 'shop'

    def get_workflow_steps(self):
        if not self.order.checked_out:
            return super(ChooseItemsView, self).get_workflow_steps()
        steps = [ShopStep, AttendeeStep]
        if (self.event.collect_housing_data and
                self.order.attendees.filter(housing_status=Attendee.NEED).exists()):
            steps.append(HousingStep)
        steps.append(PaymentStep)
        return steps

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


class AttendeesView(OrderMixin, TemplateView):
    template_name = 'brambling/event/order/attendees.html'
    current_step_slug = 'attendees'

    def get_workflow_steps(self):
        if not self.order.checked_out:
            return super(AttendeesView, self).get_workflow_steps()
        steps = [ShopStep, AttendeeStep]
        if (self.event.collect_housing_data and
                self.order.attendees.filter(housing_status=Attendee.NEED).exists()):
            steps.append(HousingStep)
        steps.append(PaymentStep)
        return steps

    def get(self, request, *args, **kwargs):
        try:
            unassigned_pass = self.order.bought_items.filter(
                item_option__item__category=Item.PASS,
                attendee__isnull=True
            ).order_by('added')[:1][0]
        except IndexError:
            return self.render_to_response(self.get_context_data())
        else:
            return HttpResponseRedirect(reverse('brambling_event_attendee_edit',
                                                kwargs={'event_slug': self.event.slug,
                                                        'pk': unassigned_pass.pk}))

    def get_context_data(self, **kwargs):
        context = super(AttendeesView, self).get_context_data(**kwargs)

        context.update({
            'errors': self.current_step.errors,
            'attendees': self.order.attendees.all(),
            'unassigned_items': self.order.bought_items.filter(attendee__isnull=True).order_by('item_option__item', 'item_option'),
        })
        return context


class AttendeeBasicDataView(OrderMixin, UpdateView):
    template_name = 'brambling/event/order/attendee_basic_data.html'
    form_class = AttendeeBasicDataForm
    current_step_slug = 'attendees'

    def get_workflow_steps(self):
        if not self.order.checked_out:
            return super(AttendeeBasicDataView, self).get_workflow_steps()
        steps = [ShopStep, AttendeeStep]
        if (self.event.collect_housing_data and
                self.order.attendees.filter(housing_status=Attendee.NEED).exists()):
            steps.append(HousingStep)
        steps.append(PaymentStep)
        return steps

    def get_form_class(self):
        fields = ('given_name', 'middle_name', 'surname', 'name_order', 'email',
                  'phone', 'liability_waiver', 'photo_consent')
        if self.event.collect_housing_data:
            fields += ('housing_status',)
        return forms.models.modelform_factory(Attendee, self.form_class, fields=fields)

    def get_object(self):
        try:
            self.event_pass = self.order.bought_items.select_related('attendee').get(
                pk=self.kwargs['pk'],
                item_option__item__category=Item.PASS
            )
        except BoughtItem.DoesNotExist:
            raise Http404
        self.event_pass.order = self.order
        return self.event_pass.attendee

    def get_initial(self):
        initial = super(AttendeeBasicDataView, self).get_initial()
        pass_count = self.order.bought_items.filter(item_option__item__category=Item.PASS).count()
        if pass_count == 1:
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
        kwargs['event_pass'] = self.event_pass
        return kwargs

    def form_valid(self, form):
        if form.instance.email == self.request.user.email:
            form.instance.person = self.request.user
            form.instance.person_confirmed = True

        self.object = form.save()
        return super(AttendeeBasicDataView, self).form_valid(form)

    def get_success_url(self):
        if self.current_step.errors:
            return self.current_step.url
        return self.current_step.next_step.url

    def get_context_data(self, **kwargs):
        context = super(AttendeeBasicDataView, self).get_context_data(**kwargs)
        context['event_pass'] = self.event_pass
        return context


class AttendeeHousingView(OrderMixin, TemplateView):
    template_name = 'brambling/event/order/attendee_housing.html'
    current_step_slug = 'housing'

    def get_workflow_steps(self):
        if not self.order.checked_out:
            return super(AttendeeHousingView, self).get_workflow_steps()
        steps = [ShopStep, AttendeeStep]
        if (self.event.collect_housing_data and
                self.order.attendees.filter(housing_status=Attendee.NEED).exists()):
            steps.append(HousingStep)
        steps.append(PaymentStep)
        return steps

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
    template_name = 'brambling/event/order/survey.html'
    context_object_name = 'order'
    current_step_slug = 'survey'

    def get_workflow_steps(self):
        if not self.order.checked_out:
            return super(SurveyDataView, self).get_workflow_steps()
        steps = [SurveyStep]
        if self.event.collect_housing_data and self.order.providing_housing:
            steps.append(HostingStep)
        return steps

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
    template_name = 'brambling/event/order/hosting.html'
    form_class = HostingForm
    current_step_slug = 'hosting'

    def get_workflow_steps(self):
        if not self.order.checked_out:
            return super(HostingView, self).get_workflow_steps()
        steps = [HostingStep]
        return steps

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
    template_name = 'brambling/event/order/summary.html'
    current_step_slug = 'payment'

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
