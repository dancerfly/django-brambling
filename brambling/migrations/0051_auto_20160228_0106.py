# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0050_auto_20160228_0059'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attendee',
            name='ef_avoid',
            field=models.ManyToManyField(related_name='attendee_avoid', verbose_name="I can't/don't want to be around", to='brambling.EnvironmentalFactor', blank=True),
        ),
        migrations.AlterField(
            model_name='attendee',
            name='ef_cause',
            field=models.ManyToManyField(related_name='attendee_cause', verbose_name='People around me may be exposed to', to='brambling.EnvironmentalFactor', blank=True),
        ),
        migrations.AlterField(
            model_name='attendee',
            name='housing_prefer',
            field=models.ManyToManyField(related_name='event_preferred_by', verbose_name='I prefer to stay somewhere that is (a/an)', to='brambling.HousingCategory', blank=True),
        ),
        migrations.AlterField(
            model_name='attendee',
            name='nights',
            field=models.ManyToManyField(to='brambling.HousingRequestNight', blank=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='members',
            field=models.ManyToManyField(related_name='events', through='brambling.EventMember', to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.AlterField(
            model_name='eventhousing',
            name='ef_avoid',
            field=models.ManyToManyField(related_name='eventhousing_avoid', verbose_name="I/We don't want in my/our home", to='brambling.EnvironmentalFactor', blank=True),
        ),
        migrations.AlterField(
            model_name='eventhousing',
            name='ef_present',
            field=models.ManyToManyField(related_name='eventhousing_present', verbose_name='People in the home may be exposed to', to='brambling.EnvironmentalFactor', blank=True),
        ),
        migrations.AlterField(
            model_name='eventhousing',
            name='housing_categories',
            field=models.ManyToManyField(related_name='eventhousing', verbose_name='Our home is (a/an)', to='brambling.HousingCategory', blank=True),
        ),
        migrations.AlterField(
            model_name='home',
            name='ef_avoid',
            field=models.ManyToManyField(related_name='home_avoid', verbose_name="I/We don't want in my/our home", to='brambling.EnvironmentalFactor', blank=True),
        ),
        migrations.AlterField(
            model_name='home',
            name='ef_present',
            field=models.ManyToManyField(related_name='home_present', verbose_name='People in my/our home may be exposed to', to='brambling.EnvironmentalFactor', blank=True),
        ),
        migrations.AlterField(
            model_name='home',
            name='housing_categories',
            field=models.ManyToManyField(related_name='homes', verbose_name='My/Our home is (a/an)', to='brambling.HousingCategory', blank=True),
        ),
        migrations.AlterField(
            model_name='organization',
            name='members',
            field=models.ManyToManyField(related_name='organizations', through='brambling.OrganizationMember', to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.AlterField(
            model_name='savedattendee',
            name='ef_avoid',
            field=models.ManyToManyField(related_name='saved_attendee_avoid', verbose_name="I can't/don't want to be around", to='brambling.EnvironmentalFactor', blank=True),
        ),
        migrations.AlterField(
            model_name='savedattendee',
            name='ef_cause',
            field=models.ManyToManyField(related_name='saved_attendee_cause', verbose_name='People around me may be exposed to', to='brambling.EnvironmentalFactor', blank=True),
        ),
        migrations.AlterField(
            model_name='savedattendee',
            name='housing_prefer',
            field=models.ManyToManyField(to='brambling.HousingCategory', verbose_name='I prefer to stay somewhere that is (a/an)', blank=True),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='bought_items',
            field=models.ManyToManyField(related_name='transactions', to='brambling.BoughtItem', blank=True),
        ),
    ]
