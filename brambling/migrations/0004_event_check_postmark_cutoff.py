# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0003_auto_20150514_2049'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='check_postmark_cutoff',
            field=models.DateField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
