# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0031_auto_20140508_0125'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='default_card',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to_field='id', blank=True, to='brambling.CreditCard'),
        ),
    ]
