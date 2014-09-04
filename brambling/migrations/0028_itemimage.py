# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0027_auto_20140901_1955'),
    ]

    operations = [
        migrations.CreateModel(
            name='ItemImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.PositiveSmallIntegerField()),
                ('image', models.ImageField(upload_to=b'')),
                ('item', models.ForeignKey(to='brambling.Item')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
