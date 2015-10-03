# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0025_auto_20151002_2116'),
    ]

    operations = [
        migrations.CreateModel(
            name='SavedAttendee',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('given_name', models.CharField(max_length=50)),
                ('middle_name', models.CharField(max_length=50, blank=True)),
                ('surname', models.CharField(max_length=50)),
                ('name_order', models.CharField(default='GMS', max_length=3, choices=[('GMS', 'Given Middle Surname'), ('SGM', 'Surname Given Middle'), ('GS', 'Given Surname'), ('SG', 'Surname Given')])),
                ('person', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('person_prefer', models.TextField(help_text='Provide a list of names, separated by line breaks.', verbose_name='I need to be placed with these people', blank=True)),
                ('person_avoid', models.TextField(help_text='Provide a list of names, separated by line breaks.', verbose_name='I do not want to be around these people', blank=True)),
                ('other_needs', models.TextField(blank=True)),
                ('ef_avoid', models.ManyToManyField(related_name='saved_attendee_avoid', null=True, verbose_name="I can't/don't want to be around", to='brambling.EnvironmentalFactor', blank=True)),
                ('ef_cause', models.ManyToManyField(related_name='saved_attendee_cause', null=True, verbose_name='People around me may be exposed to', to='brambling.EnvironmentalFactor', blank=True)),
                ('housing_prefer', models.ManyToManyField(to='brambling.HousingCategory', null=True, verbose_name='I prefer to stay somewhere that is (a/an)', blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
