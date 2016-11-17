# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('problem_builder', '0002_auto_20160121_1525'),
    ]

    operations = [
        migrations.AlterField(
            model_name='answer',
            name='course_id',
            field=models.CharField(max_length=255, db_index=True),
        ),
    ]
