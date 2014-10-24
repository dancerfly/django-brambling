# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0042_auto_20141003_2242'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='logo_image',
        ),
    ]
