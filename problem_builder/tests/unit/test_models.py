"""
Unit tests for models.
"""
from unittest.mock import MagicMock, PropertyMock

from django.test import TestCase

from problem_builder.models import Answer, delete_anonymous_user_answers


class AnswerDeleteSignalTest(TestCase):
    """ Unit tests for pre_delete signal receiver. """

    def setUp(self):
        super().setUp()
        self.course_id = 'course-v1:edX+DemoX+Demo_Course'
        self.anonymous_student_id = '123456789876543210'
        Answer.objects.create(
            name='test-course-key',
            student_id=self.anonymous_student_id,
            course_key=self.course_id,
        )
        Answer.objects.create(
            name='test-course-key-2',
            student_id=self.anonymous_student_id,
            course_key=self.course_id,
        )
        Answer.objects.create(
            name='test-course-key',
            student_id='other-user',
            course_key=self.course_id,
        )

    def test_delete_anonymous_user_answers(self):
        """
        Test the receiver function by calling it directly.
        """
        anonymous_user_id_mock = MagicMock()
        type(anonymous_user_id_mock).anonymous_user_id = PropertyMock(return_value=self.anonymous_student_id)
        delete_anonymous_user_answers(MagicMock(), instance=anonymous_user_id_mock)
        self.assertEqual(Answer.objects.filter(student_id=self.anonymous_student_id).count(), 0)
        self.assertEqual(Answer.objects.exclude(student_id=self.anonymous_student_id).count(), 1)
