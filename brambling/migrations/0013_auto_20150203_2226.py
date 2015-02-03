# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0012_auto_20150128_2256'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='transaction',
            options={'get_latest_by': 'timestamp'},
        ),
        migrations.AddField(
            model_name='transaction',
            name='event',
            field=models.ForeignKey(blank=True, to='brambling.Event', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='transaction',
            name='related_transaction',
            field=models.ForeignKey(related_name='related_transaction_set', blank=True, to='brambling.Transaction', null=True),
            preserve_default=True,
        ),
    ]
