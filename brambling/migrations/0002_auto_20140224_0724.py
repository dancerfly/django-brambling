# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='tagline',
            field=models.CharField(max_length=75, blank=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='slug',
            field=models.SlugField(),
        ),
    ]
