# encoding: utf8
from django.db import models, migrations
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('brambling', '0006_housingslot'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserInfo',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL, to_field=u'id')),
                ('dietary_restrictions_text', models.TextField(blank=True)),
                ('phone', models.CharField(max_length=50, blank=True)),
                ('ef_cause_text', models.TextField(blank=True)),
                ('ef_avoid_strong_text', models.TextField(blank=True)),
                ('ef_avoid_weak_text', models.TextField(blank=True)),
                ('user_prefer_strong_text', models.TextField(blank=True)),
                ('user_prefer_weak_text', models.TextField(blank=True)),
                ('user_avoid_strong_text', models.TextField(blank=True)),
                ('user_avoid_weak_text', models.TextField(blank=True)),
                ('dietary_restrictions', models.ManyToManyField(to='brambling.DietaryRestriction')),
                ('ef_cause', models.ManyToManyField(to='brambling.EnvironmentalFactor', blank=True)),
                ('ef_avoid_strong', models.ManyToManyField(to='brambling.EnvironmentalFactor', blank=True)),
                ('ef_avoid_weak', models.ManyToManyField(to='brambling.EnvironmentalFactor', blank=True)),
                ('user_prefer_strong', models.ManyToManyField(to=settings.AUTH_USER_MODEL, blank=True)),
                ('user_prefer_weak', models.ManyToManyField(to=settings.AUTH_USER_MODEL, blank=True)),
                ('user_avoid_strong', models.ManyToManyField(to=settings.AUTH_USER_MODEL, blank=True)),
                ('user_avoid_weak', models.ManyToManyField(to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.DeleteModel(
            name='UserPreferences',
        ),
        migrations.RemoveField(
            model_name='eventuserinfo',
            name='cause_problems_other',
        ),
        migrations.RemoveField(
            model_name='eventuserinfo',
            name='avoid_problems_other',
        ),
        migrations.RemoveField(
            model_name='eventuserinfo',
            name='request_matches',
        ),
        migrations.RemoveField(
            model_name='event',
            name='handle_housing',
        ),
        migrations.RemoveField(
            model_name='eventuserinfo',
            name='avoid_problems',
        ),
        migrations.RemoveField(
            model_name='discountcode',
            name='items',
        ),
        migrations.RemoveField(
            model_name='eventuserinfo',
            name='roles',
        ),
        migrations.RemoveField(
            model_name='eventuserinfo',
            name='cause_problems',
        ),
        migrations.RemoveField(
            model_name='eventuserinfo',
            name='request_unmatches',
        ),
        migrations.RemoveField(
            model_name='eventuserinfo',
            name='house_spaces',
        ),
        migrations.AlterField(
            model_name='eventuserinfo',
            name='car_spaces',
            field=models.SmallIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(50), django.core.validators.MinValueValidator(-1)]),
        ),
        migrations.AlterField(
            model_name='eventuserinfo',
            name='wakeup',
            field=models.CharField(max_length=5, choices=[('late', u'Get up when you get up'), ('early', u'There first thing.')]),
        ),
    ]
