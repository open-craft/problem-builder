"""
Tests of the management command to copy Answer.course_id to Answer.course_key.
"""
from django.test import TestCase
from opaque_keys.edx.keys import CourseKey

from problem_builder.management.commands.problem_builder_migrate_keys import Command
from problem_builder.models import Answer


class TestProblemBuilderMigrateKeysCommand(TestCase):
    """
    Management command unit tests.
    """
    def setUp(self):
        for i in xrange(12):
            Answer.objects.create(
                course_id=CourseKey.from_string('course-v1:Org+Course+{}'.format(i)),
                course_key=None,
            )

    def test_command(self):
        cmd = Command()
        cmd.handle(batch_size=3, sleep=0)
        for answer in Answer.objects.all():
            self.assertEqual(answer.course_key, answer.course_id)

    def test_existing_course_key(self):
        cmd = Command()
        answer = Answer.objects.get(course_id__endswith='+0')
        answer.course_key = CourseKey.from_string('course-v1:This+is+different')
        answer.save()
        cmd.handle(batch_size=3, sleep=0)
        answer.refresh_from_db()
        self.assertNotEqual(answer.course_key, answer.course_id)
