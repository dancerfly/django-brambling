# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0036_auto_20140509_0705'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='card',
            field=models.ForeignKey(to_field='id', blank=True, to='brambling.CreditCard', null=True),
            preserve_default=True,
        ),
    ]
