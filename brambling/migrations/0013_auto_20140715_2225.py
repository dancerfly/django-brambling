# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0012_auto_20140713_0644'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendee',
            name='given_name',
            field=models.CharField(default='GIVENNAME', max_length=50),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='attendee',
            name='middle_name',
            field=models.CharField(default='', max_length=50, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='attendee',
            name='name_order',
            field=models.CharField(default=b'GMS', max_length=3, choices=[(b'GMS', b'Given Middle Surname'), (b'SGM', b'Surname Given Middle'), (b'GS', b'Given Surname'), (b'SG', b'Surname Given')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='attendee',
            name='surname',
            field=models.CharField(default='SURNAME', max_length=50),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='person',
            name='given_name',
            field=models.CharField(default='GIVENNAME', max_length=50),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='person',
            name='middle_name',
            field=models.CharField(default='', max_length=50, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='person',
            name='name_order',
            field=models.CharField(default=b'GMS', max_length=3, choices=[(b'GMS', b'Given Middle Surname'), (b'SGM', b'Surname Given Middle'), (b'GS', b'Given Surname'), (b'SG', b'Surname Given')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='person',
            name='surname',
            field=models.CharField(default='SURNAME', max_length=50),
            preserve_default=False,
        ),
    ]
