# encoding: utf8
from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        #migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('brambling', '0007_event_owner'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='editors',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, blank=True),
            preserve_default=True,
        ),
    ]
