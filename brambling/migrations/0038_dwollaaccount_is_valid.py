# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0037_auto_20151219_0133'),
    ]

    operations = [
        migrations.AddField(
            model_name='dwollaaccount',
            name='is_valid',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
    ]
