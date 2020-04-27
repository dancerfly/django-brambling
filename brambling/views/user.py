from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import reverse
from django.db.models import Max, Sum, Q
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.utils.decorators import method_decorator
from django.utils.http import urlsafe_base64_decode, is_safe_url
from django.views.generic import (DetailView, CreateView, UpdateView,
                                  TemplateView, View, ListView, DeleteView)
import floppyforms.__future__ as forms

from brambling.forms.orders import AddCardForm
from brambling.forms.user import AccountForm
from brambling.forms.user import HomeForm
from brambling.forms.user import SignUpForm
from brambling.models import (Person, Home, CreditCard, Order, SavedAttendee,
                              Event, Transaction, BoughtItem,
                              EventHousing, Attendee)
from brambling.mail import ConfirmationMailer
from brambling.payment.stripe.api import (
    stripe_get_customer,
    stripe_delete_card,
)
from brambling.payment.stripe.core import (
    stripe_test_settings_valid,
    stripe_live_settings_valid,
)
from brambling.tokens import token_generators


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'registration/sign_up.html'

    def get_initial(self):
        initial = super(SignUpView, self).get_initial()
        initial = initial.copy()
        blacklist = ['password1', 'password2']
        for key, value in self.request.GET.iteritems():
            if key in blacklist:
                continue
            initial[key] = value
        return initial

    def get_success_url(self):
        redirect_to = self.request.GET.get('next', '/')
        if not is_safe_url(url=redirect_to, host=self.request.get_host()):
            redirect_to = '/'
        return redirect_to

    def get_form_kwargs(self):
        kwargs = super(SignUpView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


def send_confirmation_email_view(request, *args, **kwargs):
    if not request.user.is_authenticated():
        raise Http404
    ConfirmationMailer(
        request.user,
        site=get_current_site(request),
        secure=request.is_secure(),
    ).send([request.user.email])
    messages.add_message(request, messages.SUCCESS, "Confirmation email sent.")
    next_url = '/'
    if ('next_url' in request.GET and
            is_safe_url(url=request.GET['next_url'],
                        host=request.get_host())):
        next_url = request.GET['next_url']
    return HttpResponseRedirect(next_url)


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
        valid_token = self.generator.check_token(self.object, self.kwargs['token'])
        if valid_token:
            self.object.confirmed_email = self.object.email
            self.object.save()
        context = self.get_context_data(object=self.object)
        context['valid_token'] = valid_token
        if valid_token:
            context['claimable_orders'] = self.object.get_claimable_orders()
        return self.render_to_response(context)


class AccountView(UpdateView):
    model = Person
    form_class = AccountForm
    template_name = 'brambling/user/account.html'

    def get_object(self):
        if self.request.user.is_authenticated():
            return self.request.user
        raise Http404

    def get_form_kwargs(self):
        kwargs = super(AccountView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, "Account settings saved.")
        return super(AccountView, self).form_valid(form)

    def get_success_url(self):
        return self.request.path


class NotificationsView(UpdateView):
    model = Person
    fields = ('notify_new_purchases', 'notify_product_updates')
    template_name = 'brambling/user/notifications.html'

    def get_form_class(self):
        return forms.models.modelform_factory(Person, fields=self.fields)

    def get_object(self):
        if self.request.user.is_authenticated():
            return self.request.user
        raise Http404

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, "Notification settings saved.")
        return super(NotificationsView, self).form_valid(form)

    def get_success_url(self):
        return self.request.path


class BillingView(TemplateView):
    model = Person
    template_name = 'brambling/user/billing.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(BillingView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(BillingView, self).get_context_data(**kwargs)
        cards_qs = self.request.user.cards.filter(is_saved=True).order_by('-added')
        context.update({
            'cards': {
                'test': cards_qs.filter(api_type=CreditCard.TEST),
                'live': cards_qs.filter(api_type=CreditCard.LIVE),
            },
            'stripe_live_settings_valid': stripe_live_settings_valid(),
            'stripe_test_settings_valid': stripe_test_settings_valid(),
        })
        return context


class CreditCardAddView(TemplateView):
    template_name = 'brambling/creditcard_add.html'

    def post(self, request, *args, **kwargs):
        form = AddCardForm(request.user, api_type=kwargs['api_type'], data=request.POST)
        if form.is_valid():
            form.save()

            if ('next_url' in request.GET and
                    is_safe_url(url=request.GET['next_url'],
                                host=request.get_host())):
                next_url = request.GET['next_url']
            else:
                next_url = reverse('brambling_user_billing')
            return HttpResponseRedirect(next_url)
        self.errors = form.errors['__all__']
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreditCardAddView, self).get_context_data(**kwargs)
        context.update({
            'STRIPE_PUBLISHABLE_KEY': getattr(settings,
                                              'STRIPE_PUBLISHABLE_KEY',
                                              ''),
            'STRIPE_TEST_PUBLISHABLE_KEY': getattr(settings,
                                                   'STRIPE_TEST_PUBLISHABLE_KEY',
                                                   ''),
            'errors': getattr(self, 'errors', {}),
            'api_type': self.kwargs['api_type'],
            'LIVE': CreditCard.LIVE,
            'TEST': CreditCard.TEST,
        })
        return context


class CreditCardDeleteView(View):
    def success(self):
        return HttpResponse('')

    def delete(self, request, *args, **kwargs):
        if not request.is_ajax():
            raise Http404

        try:
            creditcard = CreditCard.objects.get(is_saved=True, pk=kwargs['pk'])
        except CreditCard.DoesNotExist:
            # Count it a success.
            return self.success()

        user = request.user

        if creditcard.person_id != user.id:
            # Maybe also just redirect?
            raise Http404

        creditcard.is_saved = False
        creditcard.save()
        customer = stripe_get_customer(creditcard.person, creditcard.api_type, create=False)
        if customer is not None:
            stripe_delete_card(customer, creditcard.stripe_card_id)
        return self.success()

    def post(self, *args, **kwargs):
        return self.delete(*args, **kwargs)


class SavedAttendeesView(ListView):
    template_name = 'brambling/user/attendee_list.html'
    model = SavedAttendee
    context_object_name = 'attendees'

    def get_queryset(self):
        if not self.request.user.is_authenticated():
            raise Http404
        return SavedAttendee.objects.filter(person=self.request.user)


class SavedAttendeeManageView(UpdateView):
    template_name = 'brambling/user/attendee_manage.html'
    model = SavedAttendee

    def get_form_class(self):
        return forms.models.modelform_factory(SavedAttendee, exclude=('person',))

    def get_queryset(self):
        if not self.request.user.is_authenticated():
            raise Http404
        return SavedAttendee.objects.filter(person=self.request.user)

    def get_object(self):
        if 'pk' not in self.kwargs:
            return None
        return super(SavedAttendeeManageView, self).get_object()

    def form_valid(self, form):
        form.instance.person = self.request.user
        return super(SavedAttendeeManageView, self).form_valid(form)

    def get_success_url(self):
        return reverse('brambling_user_attendee_edit', kwargs={'pk': self.object.pk})


class SavedAttendeeDeleteView(DeleteView):
    def get_queryset(self):
        if not self.request.user.is_authenticated():
            raise Http404
        return SavedAttendee.objects.filter(person=self.request.user)

    def get_success_url(self):
        messages.success(self.request, 'Deleted attendee: {}'.format(self.object.get_full_name()))
        return reverse('brambling_user_attendees')


class HomeView(UpdateView):
    model = Home
    form_class = HomeForm
    template_name = 'brambling/user/home.html'

    def get_object(self):
        if not self.request.user.is_authenticated():
            raise Http404
        return (Home.objects.filter(residents=self.request.user).first() or
                Home())

    def get_form_kwargs(self):
        kwargs = super(HomeView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_success_url(self):
        return reverse('brambling_home')


class ClaimOrdersView(TemplateView):
    template_name = 'brambling/user/claim_orders.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            raise Http404

        return super(ClaimOrdersView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ClaimOrdersView, self).get_context_data(**kwargs)
        context.update({
            'claimable_orders': self.request.user.get_claimable_orders().select_related('event__organization'),
            'mergeable_orders': self.request.user.get_mergeable_orders().select_related('event__organization'),
        })
        return context


class MergeOrderView(View):

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            raise Http404

        if request.user.email != request.user.confirmed_email:
            raise Http404

        pk = request.POST['pk']
        try:
            old_order = request.user.get_mergeable_orders().get(pk=pk)
        except Order.DoesNotExist:
            raise Http404

        new_order = Order.objects.get(event=old_order.event,
                                      person=request.user)

        if not new_order.get_eventhousing():
            EventHousing.objects.filter(order=old_order).update(order=new_order)
        Attendee.objects.filter(order=old_order).update(order=new_order)
        Transaction.objects.filter(order=old_order).update(order=new_order)
        BoughtItem.objects.filter(order=old_order).update(order=new_order)
        old_order.delete()

        messages.add_message(request, messages.SUCCESS,
                             "Orders successfully merged.")
        url = reverse(
            'brambling_event_attendee_list',
            kwargs={
                'event_slug': new_order.event.slug,
                'organization_slug': new_order.event.organization.slug,
            })
        return HttpResponseRedirect(url)


class ClaimOrderView(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            raise Http404

        if request.user.email != request.user.confirmed_email:
            raise Http404

        try:
            order = request.user.get_claimable_orders().get(pk=kwargs['pk'])
        except Order.DoesNotExist:
            raise Http404

        order.person = request.user
        order.save()
        messages.add_message(request, messages.SUCCESS, "Order successfully claimed.")
        return HttpResponseRedirect(reverse('brambling_claim_orders'))


class OrderHistoryView(TemplateView):
    template_name = 'brambling/user/order_history.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            raise Http404

        return super(OrderHistoryView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(OrderHistoryView, self).get_context_data(**kwargs)
        orders = Order.objects.annotate(
            last_transaction_date=Max('transactions__timestamp'),
            total=Sum('transactions__amount'),
        ).filter(
            person=self.request.user,
            total__isnull=False,
        ).select_related('event__organization').order_by('-last_transaction_date')
        context.update({
            'orders': orders,
            'claimable_orders': self.request.user.get_claimable_orders(),
        })
        return context


class OrganizeEventsView(TemplateView):
    template_name = 'brambling/user/admin_events.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            raise Http404

        return super(OrganizeEventsView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(OrganizeEventsView, self).get_context_data(**kwargs)
        admin_events = Event.objects.filter(
            Q(organization__members=self.request.user) |
            Q(members=self.request.user)
        ).order_by('-last_modified').select_related('organization').distinct()
        context['admin_events'] = admin_events
        return context


class OrganizeOrganizationsView(TemplateView):
    template_name = 'brambling/user/organizations.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            raise Http404

        return super(OrganizeOrganizationsView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(OrganizeOrganizationsView, self).get_context_data(**kwargs)
        context['organizations'] = self.request.user.organizations.order_by('-last_modified')
        return context
