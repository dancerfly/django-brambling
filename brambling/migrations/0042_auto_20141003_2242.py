# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0041_auto_20141003_2241'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventhousing',
            name='order',
            field=models.OneToOneField(related_name=b'eventhousing', to='brambling.Order'),
        ),
    ]
