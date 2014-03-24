# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0013_eventperson_person_prefer'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventperson',
            name='person_avoid',
            field=models.ManyToManyField(to='brambling.EventPerson', null=True, verbose_name='Never place me with', blank=True),
            preserve_default=True,
        ),
    ]
