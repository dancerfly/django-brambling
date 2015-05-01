# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0035_auto_20150501_0723'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='person',
            name='default_card',
        ),
    ]
