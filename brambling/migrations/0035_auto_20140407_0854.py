# encoding: utf8
from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0034_auto_20140406_2352'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Discount',
        ),
        migrations.DeleteModel(
            name='ItemDiscount',
        ),
    ]
