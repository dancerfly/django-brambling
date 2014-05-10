# encoding: utf8
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0037_payment_card'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventhousing',
            name='housing_categories_confirm',
            field=models.BooleanField(default=False, error_messages={b'blank': b'Must be marked correct.'}),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventperson',
            name='ef_avoid_confirm',
            field=models.BooleanField(default=False, error_messages={b'blank': b'Must be marked correct.'}),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventhousing',
            name='ef_avoid_confirm',
            field=models.BooleanField(default=False, error_messages={b'blank': b'Must be marked correct.'}),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventperson',
            name='ef_cause_confirm',
            field=models.BooleanField(default=False, error_messages={b'blank': b'Must be marked correct.'}),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventhousing',
            name='ef_present_confirm',
            field=models.BooleanField(default=False, error_messages={b'blank': b'Must be marked correct.'}),
            preserve_default=True,
        ),
    ]
