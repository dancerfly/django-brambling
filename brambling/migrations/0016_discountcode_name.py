# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0015_auto_20140323_0358'),
    ]

    operations = [
        migrations.AddField(
            model_name='discountcode',
            name='name',
            field=models.CharField(default='', max_length=40),
            preserve_default=False,
        ),
    ]
