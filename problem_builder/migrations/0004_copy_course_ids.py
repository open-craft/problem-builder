# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def copy_course_id_to_course_key(apps, schema_editor):
    """
    Iterates over all Answer records for which course_key is not set
    and copies the value of the course_id column into course_key.
    """
    Answer = apps.get_model('problem_builder', 'Answer')
    for answer in Answer.objects.filter(course_key__isnull=True).iterator():
        answer.course_key = answer.course_id
        answer.save()


class Migration(migrations.Migration):

    dependencies = [
        ('problem_builder', '0003_auto_20161124_0755'),
    ]

    operations = [
        migrations.RunPython(code=copy_course_id_to_course_key, reverse_code=migrations.RunPython.noop),
    ]
