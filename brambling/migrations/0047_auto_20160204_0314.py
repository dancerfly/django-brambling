# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0046_auto_20160131_0110'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invite',
            name='kind',
            field=models.CharField(max_length=10),
            preserve_default=True,
        ),
    ]
