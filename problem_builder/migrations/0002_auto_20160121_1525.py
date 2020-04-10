# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('problem_builder', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Share',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('submission_uid', models.CharField(max_length=32)),
                ('block_id', models.CharField(max_length=255, db_index=True)),
                ('notified', models.BooleanField(default=False, db_index=True)),
                ('shared_by', models.ForeignKey(related_name='problem_builder_shared_by', on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('shared_with', models.ForeignKey(related_name='problem_builder_shared_with', on_delete=models.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='share',
            unique_together=set([('shared_by', 'shared_with', 'block_id')]),
        ),
    ]
