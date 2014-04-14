# encoding: utf8
from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0022_auto_20140414_0501'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventperson',
            name='car_spaces',
            field=models.SmallIntegerField(default=0, help_text="Including the driver's seat.", validators=[django.core.validators.MaxValueValidator(50), django.core.validators.MinValueValidator(-1)]),
        ),
    ]
