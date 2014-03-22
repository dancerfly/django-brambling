# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0013_auto_20140321_0751'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='house',
            name='user_avoid_weak_text',
        ),
        migrations.RemoveField(
            model_name='house',
            name='user_prefer_weak_text',
        ),
        migrations.RemoveField(
            model_name='userinfo',
            name='ef_cause_text',
        ),
        migrations.RemoveField(
            model_name='userinfo',
            name='user_avoid_weak_text',
        ),
        migrations.RemoveField(
            model_name='house',
            name='user_avoid_strong_text',
        ),
        migrations.RemoveField(
            model_name='house',
            name='user_prefer_strong_text',
        ),
        migrations.RemoveField(
            model_name='house',
            name='ef_avoid_strong_text',
        ),
        migrations.RemoveField(
            model_name='userinfo',
            name='user_prefer_weak_text',
        ),
        migrations.RemoveField(
            model_name='userinfo',
            name='ef_avoid_weak_text',
        ),
        migrations.RemoveField(
            model_name='userinfo',
            name='ef_avoid_strong_text',
        ),
        migrations.RemoveField(
            model_name='userinfo',
            name='user_avoid_strong_text',
        ),
        migrations.RemoveField(
            model_name='userinfo',
            name='user_prefer_strong_text',
        ),
        migrations.RemoveField(
            model_name='house',
            name='ef_present_text',
        ),
        migrations.RemoveField(
            model_name='userinfo',
            name='dietary_restrictions_text',
        ),
        migrations.RemoveField(
            model_name='house',
            name='residents_text',
        ),
        migrations.RemoveField(
            model_name='house',
            name='ef_avoid_weak_text',
        ),
    ]
