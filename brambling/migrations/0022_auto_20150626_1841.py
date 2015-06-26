# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0021_auto_20150625_2103'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='method',
            field=models.CharField(max_length=7, choices=[('stripe', 'Stripe'), ('dwolla', 'Dwolla'), ('cash', 'Cash'), ('check', 'Check'), ('fake', 'Fake'), ('none', 'No balance change')]),
            preserve_default=True,
        ),
    ]
