# encoding: utf8
from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0009_eventhousing_person_prefer'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventhousing',
            name='person_avoid',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, verbose_name="I/We don't want to host", blank=True),
            preserve_default=True,
        ),
    ]
