# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0036_auto_20151219_0132'),
    ]

    operations = [
        migrations.CreateModel(
            name='DwollaAccount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('api_type', models.CharField(max_length=4, choices=[('live', 'Live'), ('test', 'Test')])),
                ('user_id', models.CharField(max_length=20)),
                ('access_token', models.CharField(max_length=50)),
                ('access_token_expires', models.DateTimeField()),
                ('refresh_token', models.CharField(max_length=50)),
                ('refresh_token_expires', models.DateTimeField()),
                ('scopes', models.CharField(max_length=100)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='dwollaaccount',
            unique_together=set([('api_type', 'user_id')]),
        ),
        migrations.AddField(
            model_name='order',
            name='dwolla_test_user_new',
            field=models.ForeignKey(related_name='order_test_set', blank=True, to='brambling.DwollaAccount', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='order',
            name='dwolla_user_new',
            field=models.ForeignKey(related_name='order_set', blank=True, to='brambling.DwollaAccount', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='organization',
            name='dwolla_test_user_new',
            field=models.ForeignKey(related_name='organization_test_set', blank=True, to='brambling.DwollaAccount', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='organization',
            name='dwolla_user_new',
            field=models.ForeignKey(related_name='organization_set', blank=True, to='brambling.DwollaAccount', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='person',
            name='dwolla_test_user_new',
            field=models.ForeignKey(related_name='person_test_set', blank=True, to='brambling.DwollaAccount', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='person',
            name='dwolla_user_new',
            field=models.ForeignKey(related_name='person_set', blank=True, to='brambling.DwollaAccount', null=True),
            preserve_default=True,
        ),
    ]
