# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0035_auto_20140509_0042'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='owners_set',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='event',
            name='cart_timeout',
            field=models.PositiveSmallIntegerField(default=15, help_text=b"Minutes before a user's cart expires."),
        ),
    ]
