import urllib

from django.conf import settings
from django.core.urlresolvers import reverse

from brambling.payment.core import LIVE
from brambling.payment.stripe.core import stripe_prep


def stripe_organization_oauth_url(organization, api_type, request):
    stripe_prep(api_type)
    if api_type == LIVE:
        client_id = getattr(settings, 'STRIPE_APPLICATION_ID', None)
    else:
        client_id = getattr(settings, 'STRIPE_TEST_APPLICATION_ID', None)
    if not client_id:
        return ''
    redirect_uri = request.build_absolute_uri(reverse('brambling_stripe_connect'))
    base_url = "https://connect.stripe.com/oauth/authorize?client_id={client_id}&response_type=code&scope=read_write&state={state}&redirect_uri={redirect_uri}"
    return base_url.format(client_id=client_id,
                           state="{}|{}".format(organization.slug, api_type),
                           redirect_uri=urllib.quote(redirect_uri))
