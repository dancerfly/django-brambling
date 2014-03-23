# encoding: utf8
from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0020_remove_dancestyle_related'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='house',
            name='user_prefer_weak',
        ),
        migrations.RemoveField(
            model_name='userinfo',
            name='user_prefer_weak',
        ),
        migrations.RemoveField(
            model_name='house',
            name='user_avoid_weak',
        ),
        migrations.RemoveField(
            model_name='event',
            name='dance_style_other',
        ),
        migrations.RemoveField(
            model_name='event',
            name='event_type_other',
        ),
        migrations.RemoveField(
            model_name='userinfo',
            name='user_avoid_weak',
        ),
        migrations.AlterField(
            model_name='userinfo',
            name='user_avoid_strong',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, verbose_name='Never place me with', blank=True),
        ),
        migrations.AlterField(
            model_name='userinfo',
            name='user_prefer_strong',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, verbose_name='Do your utmost to place me with', blank=True),
        ),
        migrations.AlterField(
            model_name='house',
            name='user_prefer_strong',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, verbose_name='Do your utmost to place here', blank=True),
        ),
        migrations.AlterField(
            model_name='userinfo',
            name='ef_avoid_strong',
            field=models.ManyToManyField(to='brambling.EnvironmentalFactor', verbose_name='Never put me somewhere with', blank=True),
        ),
        migrations.AlterField(
            model_name='userinfo',
            name='ef_avoid_weak',
            field=models.ManyToManyField(to='brambling.EnvironmentalFactor', verbose_name="I'd rather not be around", blank=True),
        ),
        migrations.AlterField(
            model_name='house',
            name='user_avoid_strong',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, verbose_name='Never place here', blank=True),
        ),
        migrations.AlterField(
            model_name='userinfo',
            name='ef_cause',
            field=models.ManyToManyField(to='brambling.EnvironmentalFactor', verbose_name='I will cause/have', blank=True),
        ),
        migrations.AlterField(
            model_name='house',
            name='ef_avoid_strong',
            field=models.ManyToManyField(to='brambling.EnvironmentalFactor', verbose_name='Not allowed in the house', blank=True),
        ),
        migrations.AlterField(
            model_name='house',
            name='ef_avoid_weak',
            field=models.ManyToManyField(to='brambling.EnvironmentalFactor', verbose_name='Preferred not in the house', blank=True),
        ),
        migrations.AlterField(
            model_name='house',
            name='ef_present',
            field=models.ManyToManyField(to='brambling.EnvironmentalFactor', verbose_name='The house has', blank=True),
        ),
    ]
