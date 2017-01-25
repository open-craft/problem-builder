"""
Unit tests for AnswerMixin.
"""
import unittest
from collections import namedtuple
from django.utils.crypto import get_random_string

from problem_builder.answer import AnswerMixin
from problem_builder.models import Answer


class TestAnswerMixin(unittest.TestCase):
    """ Unit tests for AnswerMixin. """

    FakeRuntime = namedtuple('FakeRuntime', ['course_id', 'anonymous_student_id'])

    def setUp(self):
        self.course_id = 'course-v1:edX+DemoX+Demo_Course'
        self.anonymous_student_id = '12345678987654321'

    def make_answer_mixin(self, name=None, course_id=None, student_id=None):
        if name is None:
            name = get_random_string()
        if course_id is None:
            course_id = self.course_id
        if student_id is None:
            student_id = self.anonymous_student_id
        answer_mixin = AnswerMixin()
        answer_mixin.name = name
        answer_mixin.runtime = self.FakeRuntime(course_id, student_id)
        return answer_mixin

    def test_creates_model_instance(self):
        name = 'test-model-creation'
        answer_mixin = self.make_answer_mixin(name=name)
        model = answer_mixin.get_model_object()
        self.assertEqual(model.name, name)
        self.assertEqual(model.student_id, self.anonymous_student_id)
        self.assertEqual(model.course_key, self.course_id)
        self.assertEqual(Answer.objects.get(pk=model.pk), model)

    def test_finds_instance_by_course_key(self):
        name = 'test-course-key'
        existing_model = Answer(
            name=name,
            student_id=self.anonymous_student_id,
            course_key=self.course_id,
        )
        existing_model.save()
        answer_mixin = self.make_answer_mixin(name=name)
        model = answer_mixin.get_model_object()
        self.assertEqual(model, existing_model)

    def test_works_with_long_course_keys(self):
        course_id = 'course-v1:VeryLongOrganizationName+VeryLongCourseNumber+VeryLongCourseRun'
        self.assertTrue(len(course_id) > 50)  # precondition check
        answer_mixin = self.make_answer_mixin(course_id=course_id)
        model = answer_mixin.get_model_object()
        self.assertEqual(model.course_key, course_id)
