# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0044_auto_20160112_2020'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='last_new_purchases_digest_sent',
            field=models.DateTimeField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='person',
            name='notify_new_purchases',
            field=models.CharField(default='each', max_length=5, choices=[('never', "Don't email me about new purchases"), ('each', 'Email me about every new purchase'), ('daily', 'Email me a daily report of new purchases')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='person',
            name='notify_product_updates',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
    ]
