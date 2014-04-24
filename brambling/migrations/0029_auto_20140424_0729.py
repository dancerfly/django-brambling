# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        (b'brambling', b'0028_auto_20140424_0629'),
    ]

    operations = [
        migrations.AlterField(
            model_name=b'itemoption',
            name=b'max_per_owner',
            field=models.PositiveSmallIntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name=b'itemoption',
            name=b'total_number',
            field=models.PositiveSmallIntegerField(null=True, blank=True),
        ),
    ]
