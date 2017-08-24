# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('problem_builder', '0004_copy_course_ids'),
    ]

    operations = [
        migrations.AlterField(
            model_name='answer',
            name='course_id',
            field=models.CharField(default=None, max_length=50, null=True, db_index=True, blank=True),
        ),
        migrations.AlterField(
            model_name='answer',
            name='course_key',
            field=models.CharField(max_length=255, db_index=True),
        ),
    ]
