# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0025_auto_20151002_2116'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendee',
            name='notes',
            field=models.TextField(blank=True),
            preserve_default=True,
        ),
    ]
