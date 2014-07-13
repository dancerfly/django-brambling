# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0011_auto_20140713_0559'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderdiscount',
            name='order',
            field=models.ForeignKey(default=1, to='brambling.Order'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='orderdiscount',
            unique_together=set([(b'order', b'discount')]),
        ),
        migrations.RemoveField(
            model_name='orderdiscount',
            name='event_person',
        ),
    ]
