from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from brambling.tokens import token_generators


TEMPLATE_DIR = 'brambling/mail'


class FancyMailer(object):
    key = None
    from_email = settings.DEFAULT_FROM_EMAIL

    def __init__(self, site, secure=False, key=None, from_email=None):
        if key:
            self.key = key
        if from_email:
            self.from_email = from_email
        self.site = site
        self.secure = secure

    def get_template_name(self, kind, ext=None):
        if ext is None:
            if kind == 'subject':
                ext = 'txt'
            else:
                ext = 'html'
        return "{dir}/{key}/{kind}.{ext}".format(
            dir=TEMPLATE_DIR,
            key=self.key,
            kind=kind,
            ext=ext,
        )

    def get_context_data(self):
        return {
            'site': self.site,
            'protocol': 'https' if self.secure else 'http',
        }

    def render_body(self, context, inlined=False, plaintext=False):
        if inlined:
            template_name = self.get_template_name('body_inlined')
        elif plaintext:
            template_name = self.get_template_name('body_plaintext', 'txt')
        else:
            template_name = self.get_template_name('body')
        return render_to_string(template_name, context)

    def render_subject(self, context):
        template_name = self.get_template_name('subject')
        subject = render_to_string(template_name, context)
        # Email subject *must not* contain newlines
        return ''.join(subject.splitlines())

    def render_to_response(self, inlined=False, plaintext=False):
        return HttpResponse(self.render_body(self.get_context_data(), inlined, plaintext))

    def send(self, recipient_list=None):
        if recipient_list is None:
            recipient_list = self.get_recipients()
        context = self.get_context_data()
        subject = self.render_subject(context)
        send_mail(
            subject=subject,
            message=self.render_body(context, plaintext=True),
            html_message=self.render_body(context, inlined=True),
            from_email=self.from_email,
            recipient_list=recipient_list,
            fail_silently=False,
        )

    def get_recipients(self):
        raise NotImplementedError("Subclasses must receive a recipient list "
                                  "or implement get_recipients")


class ConfirmationMailer(FancyMailer):
    key = "email_confirm"
    generator = token_generators['email_confirm']

    def __init__(self, person, *args, **kwargs):
        self.person = person
        super(ConfirmationMailer, self).__init__(*args, **kwargs)

    def get_context_data(self):
        context = super(ConfirmationMailer, self).get_context_data()
        context.update({
            'person': self.person,
            'pkb64': urlsafe_base64_encode(force_bytes(self.person.pk)),
            'email': self.person.email,
            'token': self.generator.make_token(self.person),
        })
        return context


class OrderReceiptMailer(FancyMailer):
    key = "order_receipt"

    def __init__(self, transaction, *args, **kwargs):
        self.transaction = transaction
        super(OrderReceiptMailer, self).__init__(*args, **kwargs)

    def get_context_data(self):
        context = super(OrderReceiptMailer, self).get_context_data()
        context.update({
            'transaction': self.transaction,
            'order': self.transaction.order,
            'person': self.transaction.order.person,
            'event': self.transaction.order.event,
            'unconfirmed_check_payments': (
                self.transaction.is_unconfirmed_check()
            ),
        })
        return context

    def get_recipients(self):
        order = self.transaction.order
        return [order.person.email if order.person else order.email]


class OrderAlertMailer(FancyMailer):
    key = "order_alert"

    def __init__(self, transaction, *args, **kwargs):
        self.transaction = transaction
        self.order = transaction.order
        super(OrderAlertMailer, self).__init__(*args, **kwargs)

    def get_context_data(self):
        context = super(OrderAlertMailer, self).get_context_data()
        context.update({
            'transaction': self.transaction,
            'order': self.order,
            'bought_items': self.transaction.bought_items.select_related('attendee').order_by('attendee_id', 'added'),
            'person': self.order.person,
            'event': self.order.event,
            'unconfirmed_check_payments': (
                self.transaction.is_unconfirmed_check()
            ),
        })
        return context

    def get_recipients(self):
        from brambling.models import Person
        return Person.objects.filter(
            Q(organizations=self.order.event.organization) |
            Q(events=self.order.event),
            notify_new_purchases=Person.NOTIFY_EACH,
        ).values_list('email', flat=True).distinct()


class DailyDigestMailer(FancyMailer):
    key = "daily_digest"

    def __init__(self, recipient, cutoff, *args, **kwargs):
        self.recipient = recipient
        self.cutoff = cutoff
        from brambling.models import Transaction
        self.transactions = Transaction.objects.filter(
            Q(event__members=recipient) |
            Q(event__organization__members=recipient),
            timestamp__gte=cutoff,
            transaction_type=Transaction.PURCHASE,
        ).distinct().select_related('event').prefetch_related('bought_items').order_by('event__name', 'timestamp')
        super(DailyDigestMailer, self).__init__(*args, **kwargs)

    def get_context_data(self):
        context = super(DailyDigestMailer, self).get_context_data()
        context.update({
            'recipient': self.recipient,
            'transactions': self.transactions,
            'cutoff': self.cutoff,
        })
        return context

    def get_recipients(self):
        if not self.transactions:
            return []
        return [self.recipient.email]


class InviteMailer(FancyMailer):
    def __init__(self, invite, content=None, *args, **kwargs):
        self.invite = invite
        self.content = content
        super(InviteMailer, self).__init__(*args, **kwargs)

    def get_context_data(self):
        context = super(InviteMailer, self).get_context_data()
        context.update({
            'invite': self.invite,
            'content': self.content,
        })
        return context

    def get_recipients(self):
        return [self.invite.email]
