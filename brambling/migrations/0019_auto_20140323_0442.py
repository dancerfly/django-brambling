# encoding: utf8
from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0018_auto_20140323_0420'),
    ]

    operations = [
        migrations.RenameField(
            model_name='useritem',
            old_name='paid',
            new_name='paid_at',
        ),
        migrations.RenameField(
            model_name='useritem',
            old_name='user',
            new_name='owner',
        ),
        migrations.AddField(
            model_name='useritem',
            name='paid_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, default=1, to_field=u'id'),
            preserve_default=False,
        ),
    ]
