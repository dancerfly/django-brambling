# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0018_auto_20150528_1846'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='boughtitemdiscount',
            unique_together=set([('bought_item', 'code')]),
        ),
    ]
