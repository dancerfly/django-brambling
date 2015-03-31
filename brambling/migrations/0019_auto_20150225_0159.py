# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0018_itemoption_remaining_display'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='dancestyle',
            options={'ordering': ('name',)},
        ),
        migrations.AlterModelOptions(
            name='dietaryrestriction',
            options={'ordering': ('name',)},
        ),
        migrations.AlterModelOptions(
            name='environmentalfactor',
            options={'ordering': ('name',)},
        ),
        migrations.AlterModelOptions(
            name='housingcategory',
            options={'ordering': ('name',), 'verbose_name_plural': 'housing categories'},
        ),
    ]
