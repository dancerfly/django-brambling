# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0024_auto_20140331_0033'),
    ]

    operations = [
        migrations.CreateModel(
            name='Date',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='event',
            name='housing_dates',
            field=models.ManyToManyField(to='brambling.Date', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='event',
            name='dates',
            field=models.ManyToManyField(default=1, to='brambling.Date'),
            preserve_default=False,
        ),
        migrations.RemoveField(
            model_name='event',
            name='start_date',
        ),
        migrations.RemoveField(
            model_name='event',
            name='end_date',
        ),
    ]
