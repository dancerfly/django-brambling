# encoding: utf8
from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0021_auto_20140412_2359'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventperson',
            name='person_prefer',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, verbose_name='I need to be placed with', blank=True),
        ),
        migrations.AlterField(
            model_name='home',
            name='housing_categories',
            field=models.ManyToManyField(to='brambling.HousingCategory', null=True, verbose_name='My/Our home is (a/an)', blank=True),
        ),
        migrations.AlterField(
            model_name='home',
            name='public_transit_access',
            field=models.BooleanField(default=False, verbose_name='My/Our house has easy access to public transit'),
        ),
        migrations.AlterField(
            model_name='eventperson',
            name='person_avoid',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, verbose_name='I do not want to be around', blank=True),
        ),
    ]
