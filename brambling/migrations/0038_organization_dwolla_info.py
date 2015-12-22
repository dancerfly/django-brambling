# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def copy_dwolla_forward(Organization, DwollaAccount):
    # We copy forward the live & test org accounts.
    orgs = Organization.objects.exclude(dwolla_user_id='')
    for org in orgs:
        account = DwollaAccount.objects.get_or_create(
            user_id=org.dwolla_user_id,
            api_type='live',
            defaults={
                'access_token': org.dwolla_access_token,
                'access_token_expires': org.dwolla_access_token_expires,
                'refresh_token': org.dwolla_refresh_token,
                'refresh_token_expires': org.dwolla_refresh_token_expires,
                'scopes': "send|accountinfofull|transactions",
            }
        )[0]
        org.dwolla_account = account
        org.save()

    orgs = Organization.objects.exclude(dwolla_test_user_id='')
    for org in orgs:
        account = DwollaAccount.objects.get_or_create(
            user_id=org.dwolla_test_user_id,
            api_type='test',
            defaults={
                'access_token': org.dwolla_test_access_token,
                'access_token_expires': org.dwolla_test_access_token_expires,
                'refresh_token': org.dwolla_test_refresh_token,
                'refresh_token_expires': org.dwolla_test_refresh_token_expires,
                'scopes': "send|accountinfofull|transactions",
            }
        )[0]
        org.dwolla_test_account = account
        org.save()


def do_forward_copy(apps, schema_editor):
    Organization = apps.get_model('brambling', 'Organization')
    DwollaAccount = apps.get_model('brambling', 'DwollaAccount')
    copy_dwolla_forward(Organization, DwollaAccount)


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0037_auto_20151221_2046'),
    ]

    operations = [
        migrations.RunPython(do_forward_copy, lambda *a, **k: None),
    ]
