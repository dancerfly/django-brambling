# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0038_organization_dwolla_info'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='dwolla_account',
            field=models.ForeignKey(related_name='order_set', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='brambling.DwollaAccount', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='order',
            name='dwolla_test_account',
            field=models.ForeignKey(related_name='order_test_set', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='brambling.DwollaAccount', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='organization',
            name='dwolla_account',
            field=models.ForeignKey(related_name='organization_set', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='brambling.DwollaAccount', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='organization',
            name='dwolla_test_account',
            field=models.ForeignKey(related_name='organization_test_set', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='brambling.DwollaAccount', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='person',
            name='dwolla_account',
            field=models.ForeignKey(related_name='person_set', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='brambling.DwollaAccount', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='person',
            name='dwolla_test_account',
            field=models.ForeignKey(related_name='person_test_set', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='brambling.DwollaAccount', null=True),
            preserve_default=True,
        ),
    ]
