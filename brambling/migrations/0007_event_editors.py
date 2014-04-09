# encoding: utf8
from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0006_event_owner'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='editors',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, blank=True),
            preserve_default=True,
        ),
    ]
