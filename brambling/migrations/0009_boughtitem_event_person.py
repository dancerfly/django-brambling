# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0008_boughtitem_item_option'),
    ]

    operations = [
        migrations.AddField(
            model_name='boughtitem',
            name='event_person',
            field=models.ForeignKey(to='brambling.EventPerson', to_field='id'),
            preserve_default=True,
        ),
    ]
