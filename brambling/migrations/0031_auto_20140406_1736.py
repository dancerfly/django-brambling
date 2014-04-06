# encoding: utf8
from django.db import models, migrations
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0030_auto_20140402_0513'),
    ]

    operations = [
        migrations.CreateModel(
            name='HousingCategory',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=20)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='house',
            name='ef_avoid',
            field=models.ManyToManyField(to='brambling.EnvironmentalFactor', null=True, verbose_name="I/We don't want in my/our house", blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='house',
            name='housing_categories',
            field=models.ManyToManyField(to='brambling.HousingCategory', null=True, verbose_name='Our home is (a/an)', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='person',
            name='ef_avoid',
            field=models.ManyToManyField(to='brambling.EnvironmentalFactor', null=True, verbose_name="I can't/don't want to be around", blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='person',
            name='housing_prefer',
            field=models.ManyToManyField(to='brambling.HousingCategory', null=True, verbose_name='I prefer to stay somewhere that is (a/an)', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventperson',
            name='ef_avoid',
            field=models.ManyToManyField(to='brambling.EnvironmentalFactor', null=True, verbose_name="I can't/don't want to be around", blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventhouse',
            name='housing_categories',
            field=models.ManyToManyField(to='brambling.HousingCategory', null=True, verbose_name='Our home is (a/an)', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventperson',
            name='housing_prefer',
            field=models.ManyToManyField(to='brambling.HousingCategory', null=True, verbose_name='I prefer to stay somewhere that is (a/an)', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventhouse',
            name='ef_avoid',
            field=models.ManyToManyField(to='brambling.EnvironmentalFactor', null=True, verbose_name="I/We don't want in my/our house", blank=True),
            preserve_default=True,
        ),
        migrations.RemoveField(
            model_name='house',
            name='ef_avoid_weak',
        ),
        migrations.RemoveField(
            model_name='person',
            name='ef_avoid_strong',
        ),
        migrations.RemoveField(
            model_name='person',
            name='ef_avoid_weak',
        ),
        migrations.RemoveField(
            model_name='eventperson',
            name='ef_avoid_weak',
        ),
        migrations.RemoveField(
            model_name='eventhouse',
            name='ef_avoid_weak',
        ),
        migrations.RemoveField(
            model_name='eventperson',
            name='ef_avoid_strong',
        ),
        migrations.RemoveField(
            model_name='house',
            name='ef_avoid_strong',
        ),
        migrations.RemoveField(
            model_name='eventhouse',
            name='ef_avoid_strong',
        ),
        migrations.AlterField(
            model_name='person',
            name='ef_cause',
            field=models.ManyToManyField(to='brambling.EnvironmentalFactor', null=True, verbose_name='People around me will be exposed to', blank=True),
        ),
        migrations.AlterField(
            model_name='eventperson',
            name='person_prefer',
            field=models.ManyToManyField(to='brambling.EventPerson', null=True, verbose_name='I need to be placed with', blank=True),
        ),
        migrations.AlterField(
            model_name='house',
            name='spaces_max',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Max spaces', validators=[django.core.validators.MaxValueValidator(100)]),
        ),
        migrations.AlterField(
            model_name='house',
            name='person_prefer',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, verbose_name='I/We would love to host', blank=True),
        ),
        migrations.AlterField(
            model_name='house',
            name='spaces',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Preferred spaces', validators=[django.core.validators.MaxValueValidator(100)]),
        ),
        migrations.AlterField(
            model_name='person',
            name='person_avoid',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, verbose_name='I do not want to be around', blank=True),
        ),
        migrations.AlterField(
            model_name='house',
            name='person_avoid',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, verbose_name="I/We don't want to host", blank=True),
        ),
        migrations.AlterField(
            model_name='eventhouse',
            name='person_avoid',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, verbose_name="I/We don't want to host", blank=True),
        ),
        migrations.AlterField(
            model_name='eventhouse',
            name='person_prefer',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, verbose_name='I/We would love to host', blank=True),
        ),
        migrations.AlterField(
            model_name='person',
            name='person_prefer',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, null=True, verbose_name='I need to be placed with', blank=True),
        ),
        migrations.AlterField(
            model_name='eventperson',
            name='person_avoid',
            field=models.ManyToManyField(to='brambling.EventPerson', null=True, verbose_name='I do not want to be around', blank=True),
        ),
        migrations.AlterField(
            model_name='eventperson',
            name='ef_cause',
            field=models.ManyToManyField(to='brambling.EnvironmentalFactor', null=True, verbose_name='People around me will be exposed to', blank=True),
        ),
        migrations.AlterField(
            model_name='eventhouse',
            name='ef_present',
            field=models.ManyToManyField(to='brambling.EnvironmentalFactor', null=True, verbose_name='People in the house will be exposed to', blank=True),
        ),
        migrations.AlterField(
            model_name='house',
            name='ef_present',
            field=models.ManyToManyField(to='brambling.EnvironmentalFactor', null=True, verbose_name='People in the house will be exposed to', blank=True),
        ),
    ]
