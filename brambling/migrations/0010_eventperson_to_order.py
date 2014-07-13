# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('brambling', '0009_auto_20140713_0556'),
    ]

    operations = [
        migrations.RenameModel('EventPerson', 'Order'),
        migrations.RenameModel('EventPersonDiscount', 'OrderDiscount'),
    ]
