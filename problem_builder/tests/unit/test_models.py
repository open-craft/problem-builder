"""
Unit tests for models.
"""
import unittest
from mock import MagicMock, PropertyMock

from django.contrib.auth.models import User
from django.test import TestCase

from problem_builder.models import Answer, delete_anonymous_user_answers


class AnswerDeleteSignalTest(TestCase):
    """ Unit tests for pre_delete signal receiver. """

    def setUp(self):
        super(AnswerDeleteSignalTest, self).setUp()
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

    def test_signal_receiver_connection(self):
        """
        Test the receiver function by deleting the parent User object.
        TODO: figure out how to run this test
        """
        try:
            from student.models import AnonymousUserId
        except ImportError:
            raise unittest.SkipTest('student.AnonymousUserId not available')

        user = User.objects.create(username='edx', email='edx@example.com')
        AnonymousUserId.objects.create(user=user, anonymous_user_id=self.anonymous_student_id)

        # a different anonymous id for the same user
        AnonymousUserId.objects.create(user=user, anonymous_user_id='12345678987654321-x')
        Answer.objects.create(
            name='test-course-key-3',
            student_id='12345678987654321-x',
            course_key=self.course_id,
        )

        self.assertEqual(Answer.objects.count(), 4)

        user.delete()

        # edx's answers should be deleted, leaving the one from the other user
        self.assertEqual(Answer.objects.count(), 1)
