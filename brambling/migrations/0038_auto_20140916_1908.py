# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0037_auto_20140916_0736'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='invite',
            name='status',
        ),
        migrations.AddField(
            model_name='invite',
            name='is_sent',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
