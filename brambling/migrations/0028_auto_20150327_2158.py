# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0027_auto_20150327_2140'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='check_address',
        ),
        migrations.RemoveField(
            model_name='event',
            name='check_address_2',
        ),
        migrations.RemoveField(
            model_name='event',
            name='check_city',
        ),
        migrations.RemoveField(
            model_name='event',
            name='check_country',
        ),
        migrations.RemoveField(
            model_name='event',
            name='check_payable_to',
        ),
        migrations.RemoveField(
            model_name='event',
            name='check_payment_allowed',
        ),
        migrations.RemoveField(
            model_name='event',
            name='check_postmark_cutoff',
        ),
        migrations.RemoveField(
            model_name='event',
            name='check_recipient',
        ),
        migrations.RemoveField(
            model_name='event',
            name='check_state_or_province',
        ),
        migrations.RemoveField(
            model_name='event',
            name='check_zip',
        ),
        migrations.RemoveField(
            model_name='event',
            name='dwolla_access_token',
        ),
        migrations.RemoveField(
            model_name='event',
            name='dwolla_access_token_expires',
        ),
        migrations.RemoveField(
            model_name='event',
            name='dwolla_refresh_token',
        ),
        migrations.RemoveField(
            model_name='event',
            name='dwolla_refresh_token_expires',
        ),
        migrations.RemoveField(
            model_name='event',
            name='dwolla_test_access_token',
        ),
        migrations.RemoveField(
            model_name='event',
            name='dwolla_test_access_token_expires',
        ),
        migrations.RemoveField(
            model_name='event',
            name='dwolla_test_refresh_token',
        ),
        migrations.RemoveField(
            model_name='event',
            name='dwolla_test_refresh_token_expires',
        ),
        migrations.RemoveField(
            model_name='event',
            name='dwolla_test_user_id',
        ),
        migrations.RemoveField(
            model_name='event',
            name='dwolla_user_id',
        ),
        migrations.RemoveField(
            model_name='event',
            name='editors',
        ),
        migrations.RemoveField(
            model_name='event',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='event',
            name='stripe_access_token',
        ),
        migrations.RemoveField(
            model_name='event',
            name='stripe_publishable_key',
        ),
        migrations.RemoveField(
            model_name='event',
            name='stripe_refresh_token',
        ),
        migrations.RemoveField(
            model_name='event',
            name='stripe_test_access_token',
        ),
        migrations.RemoveField(
            model_name='event',
            name='stripe_test_publishable_key',
        ),
        migrations.RemoveField(
            model_name='event',
            name='stripe_test_refresh_token',
        ),
        migrations.RemoveField(
            model_name='event',
            name='stripe_test_user_id',
        ),
        migrations.RemoveField(
            model_name='event',
            name='stripe_user_id',
        ),
        migrations.AddField(
            model_name='event',
            name='additional_editors',
            field=models.ManyToManyField(related_name='editor_events', null=True, to=settings.AUTH_USER_MODEL, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='event',
            name='organization',
            field=models.ForeignKey(to='brambling.Organization'),
            preserve_default=True,
        ),
    ]
