# encoding: utf8
from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0018_person_person_avoid'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='person_prefer',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, verbose_name='I need to be placed with', blank=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='discount',
            unique_together=set([('code', 'event')]),
        ),
    ]
