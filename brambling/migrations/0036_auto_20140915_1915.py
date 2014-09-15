# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0035_auto_20140914_2110'),
    ]

    operations = [
        migrations.AlterField(
            model_name='itemimage',
            name='item',
            field=models.ForeignKey(related_name=b'images', to='brambling.Item'),
        ),
    ]
