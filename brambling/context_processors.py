from django.conf import settings


def google_analytics(request):
    return {
        'GOOGLE_ANALYTICS_UA': getattr(settings, 'GOOGLE_ANALYTICS_UA', None),
        'GOOGLE_ANALYTICS_DOMAIN': getattr(settings, 'GOOGLE_ANALYTICS_DOMAIN', None),
    }
