from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.template import loader
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from brambling.tokens import token_generators
from brambling.utils.model_tables import *


def send_confirmation_email(person, request, secure=False,
                            generator=token_generators['email_confirm'],
                            subject_template="brambling/mail/email_confirm_subject.txt",
                            body_template="brambling/mail/email_confirm_body.txt",
                            html_body_template=None):
    if person.email == person.confirmed_email:
        return
    site = get_current_site(request)
    context = {
        'person': person,
        'pkb64': urlsafe_base64_encode(force_bytes(person.pk)),
        'email': person.email,
        'site': site,
        'token': generator.make_token(person),
        'protocol': 'https' if secure else 'http',
    }
    from_email = settings.DEFAULT_FROM_EMAIL

    subject = loader.render_to_string(subject_template,
                                      context)
    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())
    body = loader.render_to_string(body_template, context)

    if html_body_template:
        html_email = loader.render_to_string(html_body_template,
                                             context)
    else:
        html_email = None
    send_mail(subject, body, from_email, [person.email],
              html_message=html_email)
