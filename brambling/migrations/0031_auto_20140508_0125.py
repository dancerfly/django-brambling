# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0030_auto_20140505_1738'),
    ]

    operations = [
        migrations.CreateModel(
            name='CreditCard',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('stripe_card_id', models.CharField(max_length=40)),
                ('person', models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field='id')),
                ('added', models.DateTimeField(auto_now_add=True)),
                ('exp_month', models.PositiveSmallIntegerField()),
                ('exp_year', models.PositiveSmallIntegerField()),
                ('fingerprint', models.CharField(max_length=32)),
                ('last4', models.CharField(max_length=4)),
                ('brand', models.CharField(max_length=16)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='person',
            name='default_card',
            field=models.OneToOneField(null=True, to_field='id', blank=True, to='brambling.CreditCard'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='person',
            name='stripe_customer_id',
            field=models.CharField(default='', max_length=36, blank=True),
            preserve_default=False,
        ),
    ]
