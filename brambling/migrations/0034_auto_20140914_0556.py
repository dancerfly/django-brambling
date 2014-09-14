# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0033_auto_20140914_0553'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventhousing',
            name='contact_name',
            field=models.CharField(max_length=100),
        ),
    ]
