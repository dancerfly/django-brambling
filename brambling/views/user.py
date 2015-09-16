from django.conf import settings
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.utils.http import urlsafe_base64_decode, is_safe_url
from django.views.generic import (DetailView, CreateView, UpdateView,
                                  TemplateView, View)
import stripe

from brambling.forms.orders import AddCardForm
from brambling.forms.user import AccountForm, ProfileForm, BillingForm, HomeForm, SignUpForm
from brambling.models import Person, Home, CreditCard, Order
from brambling.tokens import token_generators
from brambling.mail import ConfirmationMailer
from brambling.utils.payment import (dwolla_customer_oauth_url, LIVE,
                                     stripe_test_settings_valid,
                                     stripe_live_settings_valid,
                                     dwolla_test_settings_valid,
                                     dwolla_live_settings_valid,
                                     stripe_prep)


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'registration/sign_up.html'

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
    return HttpResponseRedirect('/')


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
        return self.render_to_response(context)


class AccountView(UpdateView):
    model = Person
    form_class = AccountForm
    template_name = 'brambling/user/account.html'

    def get_object(self):
        if self.request.user.is_authenticated():
            # Do this here because _post_clean could override user's email address.
            self.claimable_orders = self.request.user.get_claimable_orders()
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

    def get_context_data(self, **kwargs):
        context = super(AccountView, self).get_context_data(**kwargs)
        context.update({
            'claimable_orders': self.claimable_orders,
        })
        return context


class ProfileView(UpdateView):
    model = Person
    form_class = ProfileForm
    template_name = 'brambling/user/profile.html'

    def get_object(self):
        if self.request.user.is_authenticated():
            return self.request.user
        raise Http404

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, "Profile settings saved.")
        return super(ProfileView, self).form_valid(form)

    def get_success_url(self):
        return self.request.path

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)
        context.update({
            'claimable_orders': self.request.user.get_claimable_orders(),
        })
        return context


class BillingView(UpdateView):
    model = Person
    form_class = BillingForm
    template_name = 'brambling/user/billing.html'

    def get_object(self):
        if self.request.user.is_authenticated():
            return self.request.user
        raise Http404

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, "Billing settings saved.")
        return super(BillingView, self).form_valid(form)

    def get_success_url(self):
        return self.request.path

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
            'dwolla_live_settings_valid': dwolla_live_settings_valid(),
            'dwolla_test_settings_valid': dwolla_test_settings_valid(),
            'claimable_orders': self.request.user.get_claimable_orders(),
        })
        if self.object.dwolla_live_can_connect():
            context['dwolla_oauth_url'] = dwolla_customer_oauth_url(
                self.request.user, LIVE, self.request)
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
            'claimable_orders': self.request.user.get_claimable_orders(),
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
        customer = None
        stripe_prep(creditcard.api_type)
        if creditcard.api_type == CreditCard.LIVE and creditcard.person.stripe_customer_id:
            customer = stripe.Customer.retrieve(creditcard.person.stripe_customer_id)
        if creditcard.api_type == CreditCard.TEST and creditcard.person.stripe_test_customer_id:
            customer = stripe.Customer.retrieve(creditcard.person.stripe_test_customer_id)
        if customer is not None:
            customer.cards.retrieve(creditcard.stripe_card_id).delete()
        return self.success()

    def post(self, *args, **kwargs):
        return self.delete(*args, **kwargs)


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

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context.update({
            'claimable_orders': self.request.user.get_claimable_orders(),
        })
        return context


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
            'unclaimable_orders': self.request.user.get_unclaimable_orders().select_related('event__organization'),
        })
        return context


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
