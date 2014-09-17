# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0036_auto_20140915_1915'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invite',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(unique=True, max_length=20)),
                ('email', models.EmailField(max_length=75)),
                ('is_sent', models.BooleanField(default=False)),
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
        migrations.AlterUniqueTogether(
            name='invite',
            unique_together=set([('email', 'content_id', 'kind')]),
        ),
        migrations.AlterField(
            model_name='eventhousing',
            name='home',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='brambling.Home', null=True),
        ),
    ]
