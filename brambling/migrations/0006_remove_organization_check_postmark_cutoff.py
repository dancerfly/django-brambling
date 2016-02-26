# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0005_copy_check_postmark_cutoff'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='organization',
            name='check_postmark_cutoff',
        ),
    ]
