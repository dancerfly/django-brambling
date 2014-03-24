# encoding: utf8
from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        #migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('brambling', '0015_house_person_avoid'),
    ]

    operations = [
        migrations.AddField(
            model_name='house',
            name='person_prefer',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, verbose_name='Do your utmost to place here', blank=True),
            preserve_default=True,
        ),
    ]
