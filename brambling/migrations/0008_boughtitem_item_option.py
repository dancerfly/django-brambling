# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0007_attendee_person_avoid'),
    ]

    operations = [
        migrations.AddField(
            model_name='boughtitem',
            name='item_option',
            field=models.ForeignKey(to='brambling.ItemOption', to_field='id'),
            preserve_default=True,
        ),
    ]
