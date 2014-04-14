# encoding: utf8
from django.db import models, migrations
import django.utils.timezone
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0020_remove_personitem_quantity'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='other_needs',
            field=models.TextField(default='', blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='eventperson',
            name='housing',
            field=models.CharField(default='need', max_length=4, choices=[('need', 'Need housing'), ('have', 'Made my own arrangements'), ('host', 'Am hosting people')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='home',
            name='public_transit_access',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='housingslot',
            name='manual',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='itemoption',
            name='max_per_owner',
            field=models.PositiveSmallIntegerField(default=1),
            preserve_default=True,
        ),
        migrations.RenameField(
            model_name='eventperson',
            old_name='other',
            new_name='other_needs',
        ),
        migrations.RemoveField(
            model_name='home',
            name='spaces',
        ),
        migrations.RemoveField(
            model_name='home',
            name='spaces_max',
        ),
        migrations.AlterField(
            model_name='event',
            name='slug',
            field=models.SlugField(help_text='URL-friendly version of the event name. Dashes, 0-9, and lower-case a-z only.', validators=[django.core.validators.RegexValidator('[a-z0-9-]+')]),
        ),
        migrations.AlterField(
            model_name='itemoption',
            name='available_start',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='event',
            name='privacy',
            field=models.CharField(default='public', help_text='Who can view this event.', max_length=7, choices=[('public', u'List publicly'), ('link', u'Visible to anyone with the link'), ('private', u'Only visible to owner and editors')]),
        ),
    ]
