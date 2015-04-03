from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.http import is_safe_url
from django.views.generic import View
from dwolla import oauth, accounts

from brambling.models import Organization, Order
from brambling.utils.payment import dwolla_prep, LIVE, dwolla_set_tokens


class DwollaConnectView(View):
    def get_object(self):
        raise NotImplementedError

    def get_success_url(self):
        raise NotImplementedError

    def get_redirect_url(self):
        raise NotImplementedError

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        redirect_url = self.object.get_dwolla_connect_url()
        api_type = request.GET['api']
        if 'code' in request.GET:
            qs = request.GET.copy()
            del qs['code']
            if qs:
                redirect_url += "?" + "&".join([k + "=" + v
                                                for k, v in qs.iteritems()])
            dwolla_prep(api_type)
            oauth_tokens = oauth.get(request.GET['code'],
                                     redirect=request.build_absolute_uri(redirect_url))
            if 'access_token' in oauth_tokens:
                token = oauth_tokens['access_token']

                # Now get account info.
                account_info = accounts.full(token)

                if api_type == LIVE:
                    self.object.dwolla_user_id = account_info['Id']
                else:
                    self.object.dwolla_test_user_id = account_info['Id']

                dwolla_set_tokens(self.object, api_type, oauth_tokens)

                self.object.save()
                messages.success(request, "Dwolla account connected!")
            elif 'error_description' in oauth_tokens:
                messages.error(request, oauth_tokens['error_description'])
            else:
                messages.error(request, "Unknown error during dwolla connection.")
        elif 'error_description' in request.GET:
            messages.error(request, request.GET['error_description'])
        else:
            messages.error(request, "Unknown error during dwolla connection.")

        return HttpResponseRedirect(self.get_success_url())


class OrganizationDwollaConnectView(DwollaConnectView):
    def get_object(self):
        return get_object_or_404(Organization, slug=self.kwargs['organization_slug'])

    def get_success_url(self):
        return reverse('brambling_organization_update',
                       kwargs={'organization_slug': self.object.slug})


class UserDwollaConnectView(DwollaConnectView):
    def get_object(self):
        if not self.request.user.is_authenticated():
            raise Http404
        return self.request.user

    def get_success_url(self):
        request = self.request
        if ('next_url' in request.GET and
                is_safe_url(url=request.GET['next_url'],
                            host=request.get_host())):
            return request.GET['next_url']
        return reverse('brambling_user_profile')


class OrderDwollaConnectView(DwollaConnectView):
    def get_object(self):
        try:
            return Order.objects.select_related(
                'event__organization',
            ).get(
                code=self.kwargs['code'],
                event__slug=self.kwargs['event_slug']
            )
        except Order.DoesNotExist:
            raise Http404

    def get_success_url(self):
        return reverse('brambling_event_order_summary',
                       kwargs={'event_slug': self.object.event.slug,
                               'organization_slug': self.object.event.organization.slug,
                               'code': self.object.code})
