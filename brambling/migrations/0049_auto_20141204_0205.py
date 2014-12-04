# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0048_auto_20141203_0219'),
    ]

    operations = [
        migrations.RenameField(
            model_name='event',
            old_name='check_latest_postmark',
            new_name='check_postmark_cutoff',
        ),
    ]
