# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0031_auto_20140910_2121'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='short_description',
            field=models.CharField(default='', max_length=140, blank=True),
            preserve_default=False,
        ),
    ]
