"""
Unit tests for Instructor Tool block
"""
import unittest

import ddt
from mock import Mock, patch
from xblock.field_data import DictFieldData

from problem_builder.instructor_tool import (COURSE_BLOCKS_API,
                                             InstructorToolBlock)


@ddt.ddt
class TestInstructorToolBlock(unittest.TestCase):
    """
    Test InstructorToolBlock with some mocked data.
    """

    def _get_block(self, block_info):
        # Build spec
        spec = ['scope_ids', 'runtime', 'has_children', 'children']
        for attr in block_info.get('attrs', []):
            spec.append(attr)
        # Assemble block
        block = Mock(spec=spec)
        scope_ids_mock = Mock()
        scope_ids_mock.usage_id = block_info.get('usage_id')
        block.scope_ids = scope_ids_mock
        block.runtime = self.runtime_mock
        block.children = []
        for attr, val in block_info.get('attrs', {}).items():
            setattr(block, attr, val)
        return block

    def setUp(self):
        self.course_id = 'course-v1:edX+DemoX+Demo_Course'
        self.runtime_mock = Mock()
        self.service_mock = Mock()
        self.runtime_mock.service = Mock(return_value=self.service_mock)
        self.runtime_mock.get_block = self._get_block
        self.runtime_mock.course_id = self.course_id
        scope_ids_mock = Mock()
        scope_ids_mock.usage_id = u'0'
        self.block = InstructorToolBlock(
            self.runtime_mock, field_data=DictFieldData({}), scope_ids=scope_ids_mock
        )

    def test_student_view_template_args(self):

        mcq_mock = Mock(return_value='Multiple Choice Question')
        # mcq_mock.ugettext()
        mrq_mock = Mock(return_value='Multiple Response Question')
        # mrq_mock.ugettext = Mock(return_value='Multiple Response Question')
        rq_mock = Mock(return_value='Rating Question')
        # rq_mock.ugettext = Mock(return_value='Rating Question')
        la_mock = Mock(return_value='Long Answer')
        # la_mock.ugettext = Mock(return_value='Long Answer')

        """
        Check if `student_view` calls rendering method of template loader
        with correct arguments.
        """
        block_choices = {
            mcq_mock.ugettext(): 'MCQBlock',
            mrq_mock.ugettext(): 'MRQBlock',
            rq_mock.ugettext(): 'RatingBlock',
            la_mock.ugettext(): 'AnswerBlock',
        }

        with patch('problem_builder.instructor_tool.loader') as patched_loader:
            patched_loader.render_django_template.return_value = u''
            self.block.student_view()
            self.service_mock.i18n_service = Mock(return_value=None)
            patched_loader.render_django_template.assert_called_once_with('templates/html/instructor_tool.html', {
                'block_choices': block_choices,
                'course_blocks_api': COURSE_BLOCKS_API,
                'root_block_id': self.course_id,
            }, i18n_service=self.service_mock)

    def test_author_view(self):
        """
        Check if author view shows appropriate message when viewing units
        containing Instructor Tool block in Studio.
        """
        fragment = self.block.author_view()
        self.assertIn('This block only works from the LMS.', fragment.content)

    def test_studio_view(self):
        """
        Check if studio view is present and shows appropriate message when
        trying to edit Instructor Tool block in Studio.
        """
        try:
            fragment = self.block.studio_view()
        except AttributeError:
            self.fail('Studio view not defined.')
        self.assertIn('This is a preconfigured block. It is not editable.', fragment.content)
