# encoding: utf8
from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0017_payment_person'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='person_avoid',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, verbose_name='I do not want to be around', blank=True),
            preserve_default=True,
        ),
    ]
