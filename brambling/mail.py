from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.template.defaultfilters import striptags
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from brambling.tokens import token_generators


def send_fancy_mail(recipient_list, subject_template, body_template, context,
                    from_email=None):
    subject = render_to_string(subject_template, context)
    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())

    body = render_to_string(body_template, context)

    send_mail(
        subject=subject,
        message=striptags(body),
        html_message=body,
        from_email=from_email or settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        fail_silently=False,
    )


def send_confirmation_email(person, site, secure=False,
                            generator=token_generators['email_confirm'],
                            subject_template="brambling/mail/email_confirm_subject.txt",
                            body_template="brambling/mail/email_confirm_body.txt"):
    if person.email == person.confirmed_email:
        return
    context = {
        'person': person,
        'pkb64': urlsafe_base64_encode(force_bytes(person.pk)),
        'email': person.email,
        'token': generator.make_token(person),
        'site': site,
        'protocol': 'https' if secure else 'http',
    }

    send_fancy_mail([person.email], subject_template, body_template, context)


def send_order_receipt(order, site, secure=False,
                       subject_template="brambling/mail/order_receipt_subject.txt",
                       body_template="brambling/mail/order_receipt_body.html"):
    context = {
        'order': order,
        'person': order.person,
        'event': order.event,
        'site': site,
        'protocol': 'https' if secure else 'http',
    }
    email = order.person.email if order.person else order.email
    send_fancy_mail([email], subject_template, body_template, context)
