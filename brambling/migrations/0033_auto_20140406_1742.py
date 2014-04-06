# encoding: utf8
from django.db import models, migrations
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0032_home'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventHousing',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('event', models.ForeignKey(to='brambling.Event', to_field=u'id')),
                ('home', models.ForeignKey(to='brambling.Home', to_field=u'id')),
                ('spaces', models.PositiveSmallIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(100)])),
                ('spaces_max', models.PositiveSmallIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(100)])),
                ('nights', models.ManyToManyField(to='brambling.Date', null=True, blank=True)),
                ('ef_present', models.ManyToManyField(to='brambling.EnvironmentalFactor', null=True, verbose_name='People in the home will be exposed to', blank=True)),
                ('ef_avoid', models.ManyToManyField(to='brambling.EnvironmentalFactor', null=True, verbose_name="I/We don't want in my/our home", blank=True)),
                ('person_prefer', models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, verbose_name='I/We would love to host', blank=True)),
                ('person_avoid', models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, verbose_name="I/We don't want to host", blank=True)),
                ('housing_categories', models.ManyToManyField(to='brambling.HousingCategory', null=True, verbose_name='Our home is (a/an)', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.DeleteModel(
            name='EventHouse',
        ),
        migrations.RemoveField(
            model_name='housingslot',
            name='house',
        ),
        migrations.RemoveField(
            model_name='person',
            name='house',
        ),
        migrations.DeleteModel(
            name='House',
        ),
        migrations.AddField(
            model_name='housingslot',
            name='home',
            field=models.ForeignKey(to='brambling.Home', default=1, to_field=u'id'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='person',
            name='home',
            field=models.ForeignKey(to_field=u'id', blank=True, to='brambling.Home', null=True),
            preserve_default=True,
        ),
    ]
