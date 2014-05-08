from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.utils.http import urlsafe_base64_decode, is_safe_url
from django.views.generic import (DetailView, CreateView, UpdateView,
                                  TemplateView, View)
import stripe

from brambling.forms.user import PersonForm, HomeForm, SignUpForm
from brambling.models import Person, Home, CreditCard
from brambling.tokens import token_generators
from brambling.utils import send_confirmation_email


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'registration/sign_up.html'
    success_url = '/'

    def get_form_kwargs(self):
        kwargs = super(SignUpView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


def send_confirmation_email_view(request, *args, **kwargs):
    if not request.user.is_authenticated():
        raise Http404
    send_confirmation_email(request.user, request, secure=request.is_secure())
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
        if not self.generator.check_token(self.object, self.kwargs['token']):
            raise Http404("Token invalid or expired.")
        self.object.confirmed_email = self.object.email
        self.object.save()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class PersonView(UpdateView):
    model = Person
    form_class = PersonForm

    def get_object(self):
        if self.request.user.is_authenticated():
            return self.request.user
        raise Http404

    def get_form_kwargs(self):
        kwargs = super(PersonView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_success_url(self):
        return self.request.path

    def get_context_data(self, **kwargs):
        context = super(PersonView, self).get_context_data(**kwargs)
        context.update({
            'cards': self.request.user.cards.order_by('-added'),
        })
        return context


class CreditCardAddView(TemplateView):
    template_name = 'brambling/creditcard_form.html'

    def post(self, request, *args, **kwargs):
        # Handle the stripe token. Create a customer if necessary.
        token = request.POST.get('stripeToken')
        user = request.user
        self.errors = {}
        if not token:
            self.errors['__all__'] = "No token was provided. Please try again."
        else:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            save_user = False
            if not user.stripe_customer_id:
                customer = stripe.Customer.create(
                    email=user.email,
                    description=user.name,
                    metadata={
                        'brambling_id': user.id,
                    },
                )
                user.stripe_customer_id = customer.id
                save_user = True
            else:
                customer = stripe.Customer.retrieve(user.stripe_customer_id)

            # This could throw some errors.
            card = customer.cards.create(card=token)

            # Check the fingerprint. Save and redirect if there's no conflict.
            # Otherwise error time!
            creditcard, created = CreditCard.objects.get_or_create(
                person=user,
                fingerprint=card.fingerprint,
                defaults={
                    'stripe_card_id': card.id,
                    'exp_month': card.exp_month,
                    'exp_year': card.exp_year,
                    'last4': card.last4,
                    'brand': card.type,
                }
            )
            if not created:
                card.delete()
                self.errors['number'] = ('You already have a card with this '
                                         'number')

            if user.default_card_id is None:
                user.default_card = creditcard
                save_user = True

            if save_user:
                user.save()

            if not self.errors:
                if ('next_url' in request.GET and
                        is_safe_url(url=request.GET['next_url'],
                                    host=request.get_host())):
                    next_url = request.GET['next_url']
                else:
                    next_url = reverse('brambling_user_profile')
                return HttpResponseRedirect(next_url)
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreditCardAddView, self).get_context_data(**kwargs)
        context.update({
            'STRIPE_PUBLISHABLE_KEY': getattr(settings,
                                              'STRIPE_PUBLISHABLE_KEY',
                                              ''),
            'errors': getattr(self, 'errors', {}),
        })
        return context


class CreditCardDeleteView(View):
    def success(self):
        return HttpResponse('')

    def delete(self, request, *args, **kwargs):
        if not request.is_ajax():
            raise Http404

        try:
            creditcard = CreditCard.objects.get(pk=kwargs['pk'])
        except CreditCard.DoesNotExist:
            # Count it a success.
            return self.success()

        user = request.user

        if creditcard.person_id != user.id:
            # Maybe also just redirect?
            raise Http404

        creditcard.delete()
        return self.success()

    def post(self, *args, **kwargs):
        return self.delete(*args, **kwargs)


class HomeView(UpdateView):
    model = Home
    form_class = HomeForm

    def get_object(self):
        if not self.request.user.is_authenticated():
            raise Http404
        return (Home.objects.filter(residents=self.request.user).first() or
                Home())

    def get_form_kwargs(self):
        kwargs = super(HomeView, self).get_form_kwargs()
        kwargs['person'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('brambling_home')
