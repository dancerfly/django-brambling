import datetime
import traceback

from django.core.management.base import BaseCommand
from django.utils import timezone

from brambling.mail import DailyDigestMailer
from brambling.models import Person


class Command(BaseCommand):
    def get_recipients(self):
        return Person.objects.filter(
            notify_new_purchases=Person.NOTIFY_DAILY,
        )

    def send_digest(self, recipient):
        cutoff = (
            recipient.last_new_purchases_digest_sent or
            (timezone.now() - datetime.timedelta(days=1))
        )
        mailer = DailyDigestMailer(
            recipient=recipient,
            cutoff=cutoff,
            site={'domain': 'dancerfly.com'},
            secure=True,
        )
        mailer.send()

    def handle(self, *args, **options):
        recipients = self.get_recipients()
        for recipient in recipients:
            try:
                self.send_digest(recipient)
            except:
                self.stderr.write("Digest send raised an error for {recipient} ({pk})".format(
                    recipient=recipient.get_full_name(),
                    pk=recipient.pk
                ))
                self.stderr.write(traceback.format_exc())
        recipients.update(last_new_purchases_digest_sent=timezone.now())
