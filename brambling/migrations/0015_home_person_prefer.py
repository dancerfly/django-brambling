# encoding: utf8
from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0014_home_person_avoid'),
    ]

    operations = [
        migrations.AddField(
            model_name='home',
            name='person_prefer',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, verbose_name='I/We would love to host', blank=True),
            preserve_default=True,
        ),
    ]
