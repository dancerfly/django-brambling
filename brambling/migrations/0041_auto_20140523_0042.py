# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0040_auto_20140522_0646'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventperson',
            name='is_completed',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.RemoveField(
            model_name='personitem',
            name='is_completed',
        ),
    ]
