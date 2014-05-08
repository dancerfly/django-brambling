# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0033_auto_20140508_0441'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='stripe_charge_id',
            field=models.CharField(default='', max_length=40, blank=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='event',
            name=b'slug',
            field=models.SlugField(help_text=b'URL-friendly version of the event name. Dashes, 0-9, and lower-case a-z only.', validators=[django.core.validators.RegexValidator(b'[a-z0-9-]+')]),
        ),
    ]
