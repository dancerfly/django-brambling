# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0052_auto_20160318_0712'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customform',
            name='form_type',
            field=models.CharField(max_length=8, choices=[('attendee', 'Attendee'), ('order', 'Order'), ('housing', 'Housing'), ('hosting', 'Hosting')]),
        ),
    ]
