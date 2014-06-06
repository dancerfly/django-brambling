# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0010_creditcard_person'),
    ]

    operations = [
        migrations.AddField(
            model_name='discount',
            name='item_option',
            field=models.ForeignKey(to='brambling.ItemOption', to_field='id'),
            preserve_default=True,
        ),
    ]
