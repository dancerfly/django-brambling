# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0011_auto_20150603_1708'),
    ]

    operations = [
        migrations.AddField(
            model_name='customformfield',
            name='help_text',
            field=models.CharField(max_length=255, blank=True),
            preserve_default=True,
        ),
    ]
