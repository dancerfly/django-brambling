# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0007_auto_20150113_0413'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Payment',
            new_name='Transaction',
        ),
    ]
