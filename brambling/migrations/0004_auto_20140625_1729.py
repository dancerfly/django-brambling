# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0003_auto_20140623_1209'),
    ]

    operations = [
        migrations.AlterField(
            model_name='creditcard',
            name='person',
            field=models.ForeignKey(to_field='id', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
