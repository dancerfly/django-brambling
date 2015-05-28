# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0009_set_stripe_metadata'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='name',
            field=models.CharField(help_text='Full pass, dance-only pass, T-shirt, socks, etc.', max_length=30),
            preserve_default=True,
        ),
    ]
