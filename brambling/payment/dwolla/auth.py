import datetime

from django.core.urlresolvers import reverse
from django.utils import timezone
from dwolla import oauth

from brambling.payment.core import LIVE
from brambling.payment.dwolla.core import dwolla_prep


DWOLLA_SCOPES = "send|accountinfofull|funding|transactions"


def dwolla_redirect_url(dwolla_obj, api_type, request, next_url=""):
    redirect_url = "{}?api={}&type={}&id={}".format(
        reverse('brambling_dwolla_connect'),
        api_type,
        dwolla_obj._meta.model_name,
        dwolla_obj.pk,
    )
    if next_url:
        redirect_url += "&next_url=" + next_url
    return request.build_absolute_uri(redirect_url)


def dwolla_oauth_url(dwolla_obj, api_type, request, next_url=""):
    dwolla_prep(api_type)
    redirect_url = dwolla_redirect_url(dwolla_obj, api_type, request, next_url)
    return oauth.genauthurl(redirect_url, scope=DWOLLA_SCOPES)


def dwolla_update_tokens(days):
    """
    Refreshes or clears all tokens that will not be refreshable within the next <days> days.
    """
    end = timezone.now() + datetime.timedelta(days=days)
    count = 0
    invalid_count = 0
    test_count = 0
    invalid_test_count = 0
    from brambling.models import DwollaAccount
    accounts = DwollaAccount.objects.filter(
        refresh_token_expires__lt=end,
        is_valid=True,
    )
    for account in accounts:
        refresh_token = account.refresh_token
        dwolla_prep(account.api_type)
        oauth_data = oauth.refresh(refresh_token)
        try:
            account.set_tokens(oauth_data)
        except ValueError:
            account.is_valid = False
            if account.api_type == LIVE:
                invalid_count += 1
            else:
                invalid_test_count += 1
        else:
            if account.api_type == LIVE:
                count += 1
            else:
                test_count += 1
        account.save()
    return count, invalid_count, test_count, invalid_test_count
