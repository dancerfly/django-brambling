# encoding: utf-8
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import TestCase, RequestFactory
import mock

from brambling.models import Organization
from brambling.payment.dwolla.auth import dwolla_redirect_url
from brambling.tests.factories import (
    OrganizationFactory,
    DwollaOrganizationAccountFactory,
)
from brambling.views.payment import DwollaConnectView


class DwollaConnectViewTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @mock.patch('dwolla.oauth.get')
    @mock.patch('dwolla.accounts.full')
    def test_dwolla_connect_updates_shared_account(self, dwolla_accounts_full, dwolla_oauth_get):
        """
        A successful connection should update the data and all
        attached models should receive the benefits immediately.

        """
        account = DwollaOrganizationAccountFactory()
        oauth_tokens = {
            'access_token': 'ACCESS_TOKEN',
            'expires_in': 1234,
            'refresh_token': 'REFRESH_TOKEN',
            'refresh_expires_in': 1234,
            'scope': 'realscopereally',
        }
        account_info = {
            'Id': account.user_id
        }
        dwolla_oauth_get.return_value = oauth_tokens
        dwolla_accounts_full.return_value = account_info
        org1 = OrganizationFactory(dwolla_test_account=account)
        org2 = OrganizationFactory(dwolla_test_account=account)

        code = 'hahaha'
        next_url = "/hello/"
        api = 'test'
        view = DwollaConnectView()
        view.request = self.factory.get('/', {
            'code': 'hahaha',
            'type': org1._meta.model_name,
            'id': org1.pk,
            'next_url': next_url,
            'api': api,
        })
        SessionMiddleware().process_request(view.request)
        MessageMiddleware().process_request(view.request)

        response = view.get(view.request)
        self.assertEqual(response.status_code, 302)
        redirect_url = dwolla_redirect_url(org1, api, view.request, next_url=view.request.GET.get('next_url'))
        dwolla_oauth_get.assert_called_once_with(
            code, redirect=redirect_url)
        dwolla_accounts_full.assert_called_once_with(
            oauth_tokens['access_token'])
        org2 = Organization.objects.get(pk=org2.pk)
        self.assertEqual(org2.dwolla_test_account.access_token, oauth_tokens['access_token'])
        self.assertEqual(org2.dwolla_test_account.scopes, oauth_tokens['scope'])
        self.assertEqual(org2.dwolla_test_account, org1.dwolla_test_account)

    @mock.patch('dwolla.oauth.get')
    @mock.patch('dwolla.accounts.full')
    def test_dwolla_connect_creates_new_account(self, dwolla_accounts_full, dwolla_oauth_get):
        """
        A successful connection for a new account shouldn't change any
        accounts attached to the old account.

        """
        account = DwollaOrganizationAccountFactory()
        oauth_tokens = {
            'access_token': 'ACCESS_TOKEN',
            'expires_in': 1234,
            'refresh_token': 'REFRESH_TOKEN',
            'refresh_expires_in': 1234,
            'scope': 'realscopereally',
        }
        account_info = {
            'Id': '123-345-567'
        }
        self.assertNotEqual(account.user_id, account_info['Id'])
        dwolla_oauth_get.return_value = oauth_tokens
        dwolla_accounts_full.return_value = account_info
        org1 = OrganizationFactory(dwolla_test_account=account)
        org2 = OrganizationFactory(dwolla_test_account=account)

        code = 'hahaha'
        next_url = "/hello/"
        api = 'test'
        view = DwollaConnectView()
        view.request = self.factory.get('/', {
            'code': 'hahaha',
            'type': org1._meta.model_name,
            'id': org1.pk,
            'next_url': next_url,
            'api': api,
        })
        SessionMiddleware().process_request(view.request)
        MessageMiddleware().process_request(view.request)

        response = view.get(view.request)
        self.assertEqual(response.status_code, 302)
        redirect_url = dwolla_redirect_url(org1, api, view.request, next_url=view.request.GET.get('next_url'))
        dwolla_oauth_get.assert_called_once_with(
            code, redirect=redirect_url)
        dwolla_accounts_full.assert_called_once_with(
            oauth_tokens['access_token'])

        org1 = Organization.objects.get(pk=org1.pk)
        org2 = Organization.objects.get(pk=org2.pk)
        self.assertNotEqual(org2.dwolla_test_account.access_token, oauth_tokens['access_token'])
        self.assertNotEqual(org2.dwolla_test_account, org1.dwolla_test_account)
        self.assertEqual(org1.dwolla_test_account.access_token, oauth_tokens['access_token'])
        self.assertEqual(org1.dwolla_test_account.scopes, oauth_tokens['scope'])
