# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0004_personitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='discount',
            name='items',
            field=models.ManyToManyField(to='brambling.Item', through='brambling.ItemDiscount'),
            preserve_default=True,
        ),
    ]
