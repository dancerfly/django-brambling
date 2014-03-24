# encoding: utf8
from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        #migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('brambling', '0018_payment_person'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='person_avoid',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, verbose_name='Never place me with', blank=True),
            preserve_default=True,
        ),
    ]
