import pytz
from django.utils import timezone


def format_as_localtime(timestamp, fmt, local_timezone):
    tz = pytz.timezone(local_timezone)
    localized = timezone.localtime(timestamp, timezone=tz)
    return localized.strftime(fmt)
