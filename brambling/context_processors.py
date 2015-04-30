from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site


def google_analytics(request):
    return {
        'GOOGLE_ANALYTICS_UA': getattr(settings, 'GOOGLE_ANALYTICS_UA', None),
        'GOOGLE_ANALYTICS_DOMAIN': getattr(settings, 'GOOGLE_ANALYTICS_DOMAIN', None),
    }


def current_site(request):
    return {
        'site': get_current_site(request),
    }
