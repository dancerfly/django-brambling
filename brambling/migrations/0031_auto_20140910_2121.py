# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0030_auto_20140910_1903'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attendee',
            name='ef_avoid',
            field=models.ManyToManyField(related_name=b'attendee_avoid', null=True, verbose_name=b"I can't/don't want to be around", to=b'brambling.EnvironmentalFactor', blank=True),
        ),
        migrations.AlterField(
            model_name='attendee',
            name='ef_cause',
            field=models.ManyToManyField(related_name=b'attendee_cause', null=True, verbose_name=b'People around me may be exposed to', to=b'brambling.EnvironmentalFactor', blank=True),
        ),
        migrations.AlterField(
            model_name='attendee',
            name='event_pass',
            field=models.OneToOneField(related_name=b'event_pass_for', to='brambling.BoughtItem'),
        ),
        migrations.AlterField(
            model_name='attendee',
            name='housing_prefer',
            field=models.ManyToManyField(related_name=b'event_preferred_by', null=True, verbose_name=b'I prefer to stay somewhere that is (a/an)', to=b'brambling.HousingCategory', blank=True),
        ),
        migrations.AlterField(
            model_name='attendee',
            name='order',
            field=models.ForeignKey(related_name=b'attendees', to='brambling.Order'),
        ),
        migrations.AlterField(
            model_name='boughtitem',
            name='attendee',
            field=models.ForeignKey(related_name=b'bought_items', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='brambling.Attendee', null=True),
        ),
        migrations.AlterField(
            model_name='boughtitem',
            name='order',
            field=models.ForeignKey(related_name=b'bought_items', to='brambling.Order'),
        ),
        migrations.AlterField(
            model_name='boughtitemdiscount',
            name='bought_item',
            field=models.ForeignKey(related_name=b'discounts', to='brambling.BoughtItem'),
        ),
        migrations.AlterField(
            model_name='creditcard',
            name='person',
            field=models.ForeignKey(related_name=b'cards', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='dates',
            field=models.ManyToManyField(related_name=b'event_dates', to=b'brambling.Date'),
        ),
        migrations.AlterField(
            model_name='event',
            name='editors',
            field=models.ManyToManyField(related_name=b'editor_events', null=True, to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='housing_dates',
            field=models.ManyToManyField(related_name=b'event_housing_dates', null=True, to=b'brambling.Date', blank=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='owner',
            field=models.ForeignKey(related_name=b'owner_events', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='eventhousing',
            name='ef_avoid',
            field=models.ManyToManyField(related_name=b'eventhousing_avoid', null=True, verbose_name=b"I/We don't want in my/our home", to=b'brambling.EnvironmentalFactor', blank=True),
        ),
        migrations.AlterField(
            model_name='eventhousing',
            name='ef_present',
            field=models.ManyToManyField(related_name=b'eventhousing_present', null=True, verbose_name=b'People in the home may be exposed to', to=b'brambling.EnvironmentalFactor', blank=True),
        ),
        migrations.AlterField(
            model_name='eventhousing',
            name='housing_categories',
            field=models.ManyToManyField(related_name=b'eventhousing', null=True, verbose_name=b'Our home is (a/an)', to=b'brambling.HousingCategory', blank=True),
        ),
        migrations.AlterField(
            model_name='home',
            name='ef_avoid',
            field=models.ManyToManyField(related_name=b'home_avoid', null=True, verbose_name=b"I/We don't want in my/our home", to=b'brambling.EnvironmentalFactor', blank=True),
        ),
        migrations.AlterField(
            model_name='home',
            name='ef_present',
            field=models.ManyToManyField(related_name=b'home_present', null=True, verbose_name=b'People in my/our home may be exposed to', to=b'brambling.EnvironmentalFactor', blank=True),
        ),
        migrations.AlterField(
            model_name='home',
            name='housing_categories',
            field=models.ManyToManyField(related_name=b'homes', null=True, verbose_name=b'My/Our home is (a/an)', to=b'brambling.HousingCategory', blank=True),
        ),
        migrations.AlterField(
            model_name='item',
            name='event',
            field=models.ForeignKey(related_name=b'items', to='brambling.Event'),
        ),
        migrations.AlterField(
            model_name='itemoption',
            name='item',
            field=models.ForeignKey(related_name=b'options', to='brambling.Item'),
        ),
        migrations.AlterField(
            model_name='orderdiscount',
            name='order',
            field=models.ForeignKey(related_name=b'discounts', to='brambling.Order'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='order',
            field=models.ForeignKey(related_name=b'payments', to='brambling.Order'),
        ),
        migrations.AlterField(
            model_name='person',
            name='default_card',
            field=models.OneToOneField(related_name=b'default_for', null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to='brambling.CreditCard'),
        ),
        migrations.AlterField(
            model_name='person',
            name='ef_avoid',
            field=models.ManyToManyField(related_name=b'person_avoid', null=True, verbose_name=b"I can't/don't want to be around", to=b'brambling.EnvironmentalFactor', blank=True),
        ),
        migrations.AlterField(
            model_name='person',
            name='ef_cause',
            field=models.ManyToManyField(related_name=b'person_cause', null=True, verbose_name=b'People around me may be exposed to', to=b'brambling.EnvironmentalFactor', blank=True),
        ),
        migrations.AlterField(
            model_name='person',
            name='groups',
            field=models.ManyToManyField(related_query_name='user', related_name='user_set', to=b'auth.Group', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of his/her group.', verbose_name='groups'),
        ),
        migrations.AlterField(
            model_name='person',
            name='home',
            field=models.ForeignKey(related_name=b'residents', blank=True, to='brambling.Home', null=True),
        ),
        migrations.AlterField(
            model_name='person',
            name='housing_prefer',
            field=models.ManyToManyField(related_name=b'preferred_by', null=True, verbose_name=b'I prefer to stay somewhere that is (a/an)', to=b'brambling.HousingCategory', blank=True),
        ),
        migrations.AlterField(
            model_name='person',
            name='user_permissions',
            field=models.ManyToManyField(related_query_name='user', related_name='user_set', to=b'auth.Permission', blank=True, help_text='Specific permissions for this user.', verbose_name='user permissions'),
        ),
        migrations.AlterField(
            model_name='refund',
            name='bought_item',
            field=models.ForeignKey(related_name=b'refunds', to='brambling.BoughtItem'),
        ),
        migrations.AlterField(
            model_name='refund',
            name='order',
            field=models.ForeignKey(related_name=b'refunds', to='brambling.Order'),
        ),
        migrations.AlterField(
            model_name='subpayment',
            name='bought_item',
            field=models.ForeignKey(related_name=b'subpayments', to='brambling.BoughtItem'),
        ),
        migrations.AlterField(
            model_name='subpayment',
            name='payment',
            field=models.ForeignKey(related_name=b'subpayments', to='brambling.Payment'),
        ),
        migrations.AlterField(
            model_name='subrefund',
            name='subpayment',
            field=models.ForeignKey(related_name=b'refunds', to='brambling.SubPayment'),
        ),
    ]
