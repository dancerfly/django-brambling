# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0002_auto_20140622_1737'),
    ]

    operations = [
        migrations.CreateModel(
            name='BoughtItemDiscount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('bought_item', models.ForeignKey(to='brambling.BoughtItem', to_field='id')),
                ('discount', models.ForeignKey(to='brambling.Discount', to_field='id')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='boughtitemdiscount',
            unique_together=set([(b'bought_item', b'discount')]),
        ),
        migrations.CreateModel(
            name='EventPersonDiscount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('discount', models.ForeignKey(to='brambling.Discount', to_field='id')),
                ('event_person', models.ForeignKey(to='brambling.EventPerson', to_field='id')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='eventpersondiscount',
            unique_together=set([(b'event_person', b'discount')]),
        ),
        migrations.AlterUniqueTogether(
            name='useddiscount',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='useddiscount',
            name='discount',
        ),
        migrations.RemoveField(
            model_name='useddiscount',
            name='event_person',
        ),
        migrations.DeleteModel(
            name='UsedDiscount',
        ),
        migrations.AddField(
            model_name='discount',
            name='item_options',
            field=models.ManyToManyField(to=b'brambling.ItemOption'),
            preserve_default=True,
        ),
        migrations.RemoveField(
            model_name='discount',
            name='item_option',
        ),
    ]
