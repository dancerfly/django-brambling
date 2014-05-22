# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('brambling', '0038_auto_20140510_0728'),
    ]

    operations = [
        migrations.CreateModel(
            name='HousingRequest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('event', models.ForeignKey(to='brambling.Event', to_field='id')),
                ('person', models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field='id')),
                ('ef_cause_confirm', models.BooleanField(default=False, error_messages={b'blank': b'Must be marked correct.'})),
                ('ef_avoid_confirm', models.BooleanField(default=False, error_messages={b'blank': b'Must be marked correct.'})),
                ('other_needs', models.TextField(blank=True)),
                ('nights', models.ManyToManyField(to='brambling.Date', null=True, blank=True)),
                ('ef_cause', models.ManyToManyField(to='brambling.EnvironmentalFactor', null=True, verbose_name=b'People around me will be exposed to', blank=True)),
                ('ef_avoid', models.ManyToManyField(to='brambling.EnvironmentalFactor', null=True, verbose_name=b"I can't/don't want to be around", blank=True)),
                ('person_prefer', models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, verbose_name=b'I need to be placed with', blank=True)),
                ('person_avoid', models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, verbose_name=b'I do not want to be around', blank=True)),
                ('housing_prefer', models.ManyToManyField(to='brambling.HousingCategory', null=True, verbose_name=b'I prefer to stay somewhere that is (a/an)', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
