# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
from django.utils.crypto import get_random_string


def forwards_func(apps, schema_editor):
    Order = apps.get_model("brambling", "Order")
    db_alias = schema_editor.connection.alias
    for order in Order.objects.using(db_alias).all():
        code = get_random_string(8)
        while Order.objects.using(db_alias).filter(code=code).exists():
            code = get_random_string(8)
        order.code = code
        order.save()


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0016_auto_20140717_1716'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='code',
            field=models.CharField(default='', max_length=8, db_index=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='order',
            name='person',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.RunPython(
            forwards_func,
        )
    ]
