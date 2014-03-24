# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0012_eventperson_person'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventperson',
            name='person_prefer',
            field=models.ManyToManyField(to='brambling.EventPerson', null=True, verbose_name='Do your utmost to place me with', blank=True),
            preserve_default=True,
        ),
    ]
