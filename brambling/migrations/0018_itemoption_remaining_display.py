# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0017_auto_20150214_0028'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemoption',
            name='remaining_display',
            field=models.CharField(default=b'both', max_length=9, choices=[(b'both', 'Remaining / Total'), (b'total', 'Total only'), (b'remaining', 'Remaining only'), (b'hidden', "Don't display")]),
            preserve_default=True,
        ),
    ]
