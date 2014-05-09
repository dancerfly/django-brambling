# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0034_auto_20140508_0918'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('person', models.ForeignKey(to=settings.AUTH_USER_MODEL, to_field='id')),
                ('event', models.ForeignKey(to='brambling.Event', to_field='id')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='personitem',
            name='is_completed',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='personitem',
            name='cart',
            field=models.ForeignKey(to_field='id', blank=True, to='brambling.Cart', null=True),
            preserve_default=True,
        ),
        migrations.RenameField(
            model_name='event',
            old_name=b'reservation_timeout',
            new_name='cart_timeout',
        ),
        migrations.AlterField(
            model_name='personitem',
            name=b'added',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='personitem',
            name=b'status',
            field=models.CharField(default=b'unpaid', max_length=8, choices=[(b'unpaid', 'Unpaid'), (b'partial', 'Partially paid'), (b'paid', 'Paid'), (b'refunded', 'Refunded')]),
        ),
    ]
