# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0031_auto_20150428_1955'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customformfield',
            name='name',
            field=models.CharField(max_length=255),
            preserve_default=True,
        ),
    ]
