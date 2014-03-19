# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0007_auto_20140319_1648'),
    ]

    operations = [
        migrations.DeleteModel(
            name='DiscountCode',
        ),
        migrations.DeleteModel(
            name='UserDiscount',
        ),
        migrations.DeleteModel(
            name='ItemDiscount',
        ),
    ]
