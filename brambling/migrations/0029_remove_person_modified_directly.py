# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0028_auto_20151003_2301'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='person',
            name='modified_directly',
        ),
    ]
