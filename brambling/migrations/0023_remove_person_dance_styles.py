# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0022_auto_20150908_1533'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='person',
            name='dance_styles',
        ),
    ]
