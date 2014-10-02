# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0038_auto_20140919_2103'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='tagline',
        ),
    ]
