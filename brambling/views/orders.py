from django.conf import settings
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.forms.models import model_to_dict
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView, View, UpdateView, FormView
import floppyforms.__future__ as floppyforms

from brambling.forms.orders import (SavedCardPaymentForm, OneTimePaymentForm,
                                    HostingForm, AttendeeBasicDataForm,
                                    AttendeeHousingDataForm, DwollaPaymentForm,
                                    SurveyDataForm, CheckPaymentForm, TransferForm)
from brambling.mail import OrderReceiptMailer, OrderAlertMailer
from brambling.models import (BoughtItem, ItemOption, Discount, Order,
                              Attendee, EventHousing, Event, Transaction,
                              Invite, Person, SavedAttendee)
from brambling.utils.payment import dwolla_oauth_url
from brambling.views.utils import (get_event_admin_nav, ajax_required,
                                   clear_expired_carts, Workflow, Step,
                                   WorkflowMixin)


class RactiveShopView(TemplateView):
    current_step_slug = 'shop'
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
        try:
            order = Order.objects.get(event=event, person=self.request.user)
        except:
            order = None

        # TODO: This will never allow anonymous users to get past the
        # shopping page, because their orders are stored in the session.
        # Probably we need to refactor OrderViewSet.create() to make an
        # Order.objects.from_request() method that gets used across the board.
        # And/or find a better way to store workflow information.

        context['event'] = event
        context['editable_by_user'] = editable_by_user
        context['workflow'] = RegistrationWorkflow(event=event, order=order)
        return context


class OrderStep(Step):
    view_name = None

    @property
    def url(self):
        kwargs = {
            'event_slug': self.workflow.event.slug,
            'organization_slug': self.event.organization.slug,
        }
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

    def __init__(self, *args, **kwargs):
        super(AttendeeStep, self).__init__(*args, **kwargs)
        order = self.workflow.order
        valid_statuses = (BoughtItem.RESERVED, BoughtItem.UNPAID, BoughtItem.BOUGHT)
        if order:
            self.bought_items = order.bought_items.filter(status__in=valid_statuses).order_by('item_name', 'item_option_name')
            self.attendees = order.attendees.order_by('pk').select_related('saved_attendee')
        else:
            self.bought_items = []
            self.attendees = []

    def _is_completed(self):
        if not self.workflow.order:
            return False

        for item in self.bought_items:
            if item.attendee_id is None:
                return False

        if self.workflow.event.collect_housing_data:
            for attendee in self.attendees:
                if attendee.housing_status == Attendee.NEED and not attendee.housing_completed:
                    return False

        return True

    def get_errors(self):
        errors = {}

        attendee_map = {}
        for attendee in self.attendees:
            attendee.items = []
            attendee_map[attendee.pk] = attendee
        for item in self.bought_items:
            if item.attendee_id in attendee_map:
                item.attendee = attendee_map[item.attendee_id]
                item.attendee.items.append(item)
            else:
                errors['bought_items'] = ['All items in order must be assigned to an attendee.']

        for attendee in self.attendees:
            attendee.errors = []
            if len(attendee.items) == 0:
                attendee.errors.append('Must have at least one item.')
            if not attendee.basic_completed:
                attendee.errors.append('Missing basic data.')
            if self.workflow.event.collect_housing_data:
                if attendee.housing_status == Attendee.NEED and not attendee.housing_completed:
                    attendee.errors.append('Missing housing data.')
            if attendee.errors:
                errors.setdefault('attendees', {})[attendee.pk] = attendee.errors

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
    step_classes = [ShopStep, AttendeeStep, SurveyStep,
                    HostingStep, OrderEmailStep, PaymentStep]


class ShopWorkflow(Workflow):
    step_classes = [ShopStep, AttendeeStep, HostingStep, PaymentStep]


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

    def get_order(self, create=False):
        # Never create for invite-only events.
        if self.event.privacy in (Event.HALF_PUBLIC, Event.INVITED):
            create = False

        order_kwargs = {
            'event': self.event,
            'request': self.request,
            'create': create,
        }
        try:
            return Order.objects.for_request(**order_kwargs)[0]
        except Order.DoesNotExist:
            return None

    def get_context_data(self, **kwargs):
        context = super(OrderMixin, self).get_context_data(**kwargs)
        context.update({
            'event': self.event,
            'order': self.order,
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
        return kwargs


class OrderCodeRedirectView(OrderMixin, View):

    def dispatch(self, request, *args, **kwargs):
        self.event = get_object_or_404(
            Event.objects.select_related('organization'),
            slug=kwargs['event_slug'],
            organization__slug=kwargs['organization_slug'])
        if not self.event.viewable_by(request.user):
            raise Http404
        try:
            order = Order.objects.get(event=self.event, code=kwargs['code'])
        except Order.DoesNotExist:
            raise Http404

        session_code = Order.objects._get_session_code(request, self.event)
        if ((order.code == session_code and not request.user.is_authenticated()) or
                (request.user.is_authenticated() and request.user.id == order.person_id)):
            # If the user is authenticated and this is their order (or if they're not
            # authenticated but it's in their session) redirect to the order summary.
            url = reverse('brambling_event_order_summary', kwargs={
                'event_slug': self.event.slug,
                'organization_slug': self.event.organization.slug,
            })
        elif order.person_id is not None:
            # It's got an account attached, but this person isn't logged in
            # under that account.
            url = "{}?next={}".format(reverse('login'), request.path)
            messages.error(request, "Log in to view order {} if you are its owner.".format(order.code))
        elif request.user.is_authenticated() and request.user.email == order.email:
            # The current user is logged in and *is* the owner. Send them to claim it.
            url = reverse('brambling_claim_orders')
            messages.error(request, "Claim order {} to view it.".format(order.code))
        elif Person.objects.filter(email=order.email).exists():
            # An account exists with the same email as this order. Send them to login.
            url = "{}?next={}".format(reverse('login'), reverse('brambling_claim_orders'))
            messages.error(request, "Log in to claim order {} and view it".format(order.code))
        else:
            # Otherwise, send them to sign up.
            url = "{}?next={}".format(reverse('brambling_signup'), reverse('brambling_claim_orders'))
            messages.error(request, "Create an account to claim order {} and view it".format(order.code))
        return HttpResponseRedirect(url)


class AddToOrderView(OrderMixin, View):
    @method_decorator(ajax_required)
    def post(self, request, *args, **kwargs):
        clear_expired_carts(self.event)

        if self.order is None:
            return JsonResponse({'success': False, 'error': "Registration for this event is restricted."})

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

    def get_order(self, create=True):
        return super(AddToOrderView, self).get_order(create)


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
        if self.order is None:
            return JsonResponse({'success': False, 'error': "Registration for this event is restricted."})

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

    def get_order(self, create=True):
        return super(ApplyDiscountView, self).get_order(create)


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
        if not self.current_step.attendees:
            kwargs = {
                'event_slug': self.event.slug,
                'organization_slug': self.event.organization.slug,
            }
            return HttpResponseRedirect(reverse('brambling_event_attendee_add',
                                                kwargs=kwargs))
        self.unassigned_items = [item for item in self.current_step.bought_items
                                 if item.attendee_id is None]
        # If there's only one attendee, automatically assign items:
        if len(self.current_step.attendees) == 1:
            for item in self.unassigned_items:
                item.attendee = self.current_step.attendees[0]
                item.save()
            self.unassigned_items = []
        # If GET params say to skip this step (i.e., when there's only one
        # attendee and the user is coming from the attendee form):
        if request.GET.get('skip'):
            return HttpResponseRedirect(reverse(
                                        self.current_step.next_step.view_name,
                                        kwargs=kwargs
                                        ))
        return self.render_to_response(self.get_context_data())

    def get_context_data(self, **kwargs):
        context = super(AttendeesView, self).get_context_data(**kwargs)

        context.update({
            'errors': self.current_step.errors,
            'attendees': self.current_step.attendees,
            'unassigned_items': self.unassigned_items,
        })
        return context


class AttendeeBasicDataView(OrderMixin, WorkflowMixin, TemplateView):
    template_name = 'brambling/event/order/attendee_basic_data.html'
    current_step_slug = 'attendees'
    workflow_class = RegistrationWorkflow

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        initial = model_to_dict(self.object.saved_attendee) if self.object.saved_attendee else {}

        self.basic_data_form = self.get_basic_data_form(initial=initial)
        self.housing_form = None
        if self.event.collect_housing_data:
            self.housing_form = self.get_housing_form(initial=initial)
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        initial = model_to_dict(self.object.saved_attendee) if self.object.saved_attendee else {}

        created = not self.object.pk
        all_valid = True
        self.basic_data_form = self.get_basic_data_form(initial=initial)

        if not self.basic_data_form.is_valid():
            all_valid = False

        self.housing_form = None
        if self.event.collect_housing_data and self.basic_data_form.cleaned_data.get('housing_status') == Attendee.NEED:
            self.housing_form = self.get_housing_form(initial=initial)
            if not self.housing_form.is_valid():
                all_valid = False

        if all_valid:
            if (self.request.user.is_authenticated() and
                    self.object.email == self.request.user.email):
                self.object.person = self.request.user

            self.basic_data_form.save()
            if self.housing_form:
                self.housing_form.save()
            success_url = self.get_success_url()
            # If they are only saving a single attendee, add a GET param to
            # skip rendering the attendee assignment screen. (Received by
            # AttendeesView above.)
            if (len(self.workflow.steps['attendees'].attendees) == 1 and
                    self.request.POST.get('next') != 'add' and
                    created):
                success_url = "{0}?skip=1".format(success_url)
            return HttpResponseRedirect(success_url)
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_success_url(self):
        if self.request.POST.get('next') == 'add':
            view = 'brambling_event_attendee_add'
        else:
            view = 'brambling_event_attendee_list'
        return reverse(view, kwargs={
            'event_slug': self.event.slug,
            'organization_slug': self.event.organization.slug,
        })

    def get_object(self):
        if 'pk' not in self.kwargs:
            saved_attendee = None
            if self.request.user.is_authenticated() and 'saved_attendee' in self.request.GET:
                try:
                    saved_attendee = SavedAttendee.objects.get(
                        person=self.request.user,
                        pk=self.request.GET['saved_attendee'],
                    )
                except SavedAttendee.DoesNotExist:
                    pass
            return Attendee(order=self.order, saved_attendee=saved_attendee)
        # Saves a query and preserves any error information
        for attendee in self.current_step.attendees:
            if attendee.pk == int(self.kwargs['pk']):
                return attendee
        raise Http404

    def get_basic_data_form(self, initial=None):
        fields = ('given_name', 'middle_name', 'surname', 'name_order', 'email',
                  'phone', 'liability_waiver', 'photo_consent')
        if self.event.collect_housing_data:
            fields += ('housing_status',)
        cls = floppyforms.models.modelform_factory(
            Attendee,
            AttendeeBasicDataForm,
            fields=fields
        )

        kwargs = {
            'prefix': "basic",
            'order': self.order,
            'instance': self.object,
            'initial': initial,
        }
        if self.request.method == 'POST':
            kwargs['data'] = self.request.POST
        return cls(**kwargs)

    def get_housing_form(self, initial=None):
        kwargs = {
            'prefix': "housing",
            'instance': self.object,
            'initial': initial,
        }
        if self.request.method == 'POST':
            kwargs['data'] = self.request.POST
        return AttendeeHousingDataForm(**kwargs)

    def get_context_data(self, **kwargs):
        context = super(AttendeeBasicDataView, self).get_context_data(**kwargs)
        context.update({
            'object': self.object,
            'attendee': self.object,
            'attendees': self.current_step.attendees,
            'bought_items': self.current_step.bought_items,
            'basic_data_form': self.basic_data_form,
            'housing_form': self.housing_form,
            'saved_attendee': self.object.saved_attendee,
        })
        if self.object.pk is None and self.order.person:
            context['saved_attendees'] = self.order.person.savedattendee_set.order_by(
                '-last_modified',
            ).exclude(
                attendee__order=self.order,
            )
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
        return reverse('brambling_event_order_summary', kwargs=kwargs)


class OrderEmailView(OrderMixin, WorkflowMixin, UpdateView):
    template_name = 'brambling/event/order/email.html'
    current_step_slug = 'email'
    workflow_class = RegistrationWorkflow

    def get_form_class(self):
        cls = floppyforms.models.modelform_factory(Order, floppyforms.ModelForm, fields=('email',))
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
                method=Transaction.NONE,
                transaction_type=Transaction.PURCHASE,
                is_confirmed=True,
                api_type=self.event.api_type,
                event=self.event,
                order=self.order,
            )
            self.order.mark_cart_paid(payment)
            if not self.event.is_frozen:
                self.event.is_frozen = True
                self.event.save()
            self.send_email()
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
                self.send_email()
            elif form:
                for error in form.non_field_errors():
                    messages.error(request, error)

        if valid:
            if not self.order.person:
                url = reverse('brambling_event_order_summary', kwargs={
                    'event_slug': self.event.slug,
                    'organization_slug': self.event.organization.slug
                })
                return HttpResponseRedirect(url)
            return HttpResponseRedirect('')
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def send_email(self):
        summary_data = self.order.get_summary_data()
        email_kwargs = {
            'order': self.order,
            'summary_data': summary_data,
            'site': get_current_site(self.request),
            'secure': self.request.is_secure()
        }
        OrderReceiptMailer(**email_kwargs).send()
        OrderAlertMailer(**email_kwargs).send()

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
        account = dwolla_obj.get_dwolla_account(self.event.api_type)
        dwolla_connected = account and account.is_connected()
        dwolla_can_connect = dwolla_obj.dwolla_can_connect(self.event.api_type)
        if dwolla_can_connect:
            kwargs = {
                'event_slug': self.event.slug,
                'organization_slug': self.event.organization.slug,
            }
            next_url = reverse('brambling_event_order_summary', kwargs=kwargs)
            context['dwolla_oauth_url'] = dwolla_oauth_url(
                dwolla_obj, self.event.api_type, self.request, next_url)
        if dwolla_connected:
            context.update({
                'dwolla_is_connected': True,
                'dwolla_user_id': account.user_id
            })
        context.update(self.summary_data)
        return context


class TransferView(OrderMixin, WorkflowMixin, FormView):
    form_class = TransferForm
    template_name = 'brambling/event/order/transfer.html'
    workflow_class = RegistrationWorkflow
    current_step_slug = 'payment'

    def get_initial(self):
        return self.request.GET

    def get_form_kwargs(self):
        kwargs = super(TransferView, self).get_form_kwargs()
        kwargs.update({
            'order': self.order,
        })
        return kwargs

    def form_valid(self, form):
        invite, created = Invite.objects.get_or_create_invite(
            email=form.cleaned_data['email'],
            user=self.request.user if self.request.user.is_authenticated() else None,
            kind=Invite.TRANSFER,
            content_id=form.cleaned_data['bought_item'].pk,
        )
        if created:
            invite.send(
                content=form.cleaned_data['bought_item'],
                secure=self.request.is_secure(),
                site=get_current_site(self.request)
            )
        return super(TransferView, self).form_valid(form)

    def get_success_url(self):
        return reverse('brambling_event_order_summary', kwargs=self.kwargs)
