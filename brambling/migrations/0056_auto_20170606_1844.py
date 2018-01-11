# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0055_auto_20170601_2144'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProcessedStripeEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('api_type', models.CharField(default=b'live', max_length=4, choices=[(b'live', 'Live'), (b'test', 'Test')])),
                ('stripe_event_id', models.CharField(max_length=255)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.DeleteModel(
            name='ProcessedStripeLiveEvent',
        ),
        migrations.DeleteModel(
            name='ProcessedStripeTestEvent',
        ),
        migrations.AlterUniqueTogether(
            name='processedstripeevent',
            unique_together=set([('api_type', 'stripe_event_id')]),
        ),
    ]
