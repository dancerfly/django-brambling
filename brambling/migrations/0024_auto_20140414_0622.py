# encoding: utf8
from django.db import models, migrations
from django.conf import settings


#see https://code.djangoproject.com/ticket/22432
class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0023_auto_20140414_0507'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='eventperson',
            name='person_prefer',
        ),
        migrations.RemoveField(
            model_name='eventperson',
            name='person_avoid',
        ),
        migrations.AddField(
            model_name='eventperson',
            name='person_prefer',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, verbose_name='I need to be placed with', blank=True),
        ),
        migrations.AddField(
            model_name='eventperson',
            name='person_avoid',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, verbose_name='I do not want to be around', blank=True),
        ),
    ]
