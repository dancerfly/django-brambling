from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from brambling.payment.dwolla.auth import dwolla_update_tokens


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            '--days',
            action='store',
            dest='days',
            default=15,
            help='Number of days ahead of time to update refresh tokens.',
        ),
    )

    def handle(self, *args, **options):
        try:
            days = int(options['days'])
        except ValueError:
            raise CommandError("Days must be an integer value.")
        self.stdout.write("Updating dwolla tokens...")
        self.stdout.flush()
        count, cleared_count, test_count, cleared_test_count = dwolla_update_tokens(days)
        self.stdout.write("Test tokens updated: {}".format(test_count))
        self.stdout.write("Test tokens cleared: {}".format(cleared_test_count))
        self.stdout.write("Live tokens updated: {}".format(count))
        self.stdout.write("Live tokens cleared: {}".format(cleared_count))
        self.stdout.flush()
