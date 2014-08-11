# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('brambling', '0022_attendee_event_pass'),
    ]

    operations = [
        migrations.CreateModel(
            name='Refund',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('amount', models.DecimalField(max_digits=5, decimal_places=2)),
                ('bought_item', models.ForeignKey(to='brambling.BoughtItem')),
                ('issuer', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('order', models.ForeignKey(to='brambling.Order')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SubPayment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('amount', models.DecimalField(max_digits=5, decimal_places=2)),
                ('bought_item', models.ForeignKey(to='brambling.BoughtItem')),
                ('payment', models.ForeignKey(to='brambling.Payment')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='subpayment',
            unique_together=set([(b'payment', b'bought_item')]),
        ),
        migrations.CreateModel(
            name='SubRefund',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('amount', models.DecimalField(max_digits=5, decimal_places=2)),
                ('method', models.CharField(max_length=6, choices=[(b'stripe', b'Stripe')])),
                ('remote_id', models.CharField(max_length=40, blank=True)),
                ('refund', models.ForeignKey(to='brambling.Refund')),
                ('subpayment', models.ForeignKey(to='brambling.SubPayment')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='boughtitem',
            name='payments',
            field=models.ManyToManyField(to=b'brambling.Payment', through='brambling.SubPayment'),
            preserve_default=True,
        ),
    ]
