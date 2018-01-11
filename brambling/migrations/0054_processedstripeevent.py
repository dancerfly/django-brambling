# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0053_auto_20160425_2258'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProcessedStripeEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('stripe_event_id', models.CharField(max_length=35)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
