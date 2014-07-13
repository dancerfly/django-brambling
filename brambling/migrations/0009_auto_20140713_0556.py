# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0008_auto_20140705_2010'),
    ]

    operations = [
        migrations.AlterField(
            model_name='discount',
            name='code',
            field=models.CharField(help_text=b'Allowed characters: 0-9, a-z, A-Z, space, and \'"~', max_length=20, validators=[django.core.validators.RegexValidator(b'[0-9A-Za-z \'"~]+')]),
        ),
    ]
