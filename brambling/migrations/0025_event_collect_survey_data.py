# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0024_auto_20140608_2253'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='collect_survey_data',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
    ]
