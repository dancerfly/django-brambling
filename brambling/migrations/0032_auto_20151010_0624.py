# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0031_auto_20151010_0621'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='person',
            name='dietary_restrictions',
        ),
        migrations.DeleteModel(
            name='DietaryRestriction',
        ),
    ]
