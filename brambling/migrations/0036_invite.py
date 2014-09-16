# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0035_auto_20140914_2110'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invite',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(unique=True, max_length=20)),
                ('email', models.EmailField(max_length=75)),
                ('status', models.CharField(max_length=8, choices=[(b'sent', 'Sent'), (b'accepted', 'Accepted'), (b'rejected', 'Rejected')])),
                ('kind', models.CharField(max_length=6, choices=[(b'home', 'Home'), (b'editor', 'Editor')])),
                ('content_id', models.IntegerField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
