"""
Unit tests for Instructor Tool block
"""
import ddt
import unittest
from mock import Mock, patch
from xblock.field_data import DictFieldData
from problem_builder import InstructorToolBlock


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
        self.runtime_mock = Mock()
        self.runtime_mock.get_block = self._get_block
        scope_ids_mock = Mock()
        scope_ids_mock.usage_id = u'0'
        self.block = InstructorToolBlock(
            self.runtime_mock, field_data=DictFieldData({}), scope_ids=scope_ids_mock
        )
        self.block.children = [
            # No attributes: Prefer usage_id
            {'usage_id': u'1'},
            # Single attribute: Prefer attribute that's present
            {'usage_id': u'2', 'preferred_attr': 'question', 'attrs': {'question': 'question'}},
            {'usage_id': u'3', 'preferred_attr': 'name', 'attrs': {'name': 'name'}},
            {'usage_id': u'4', 'preferred_attr': 'display_name', 'attrs': {'display_name': 'display_name'}},
            # Two attributes (question, name): Prefer question
            {
                'usage_id': u'5',
                'preferred_attr':
                'question', 'attrs': {'question': 'question', 'name': 'name'}
            },
            # Two attributes (question, display_name): Prefer question
            {
                'usage_id': u'6',
                'preferred_attr': 'question',
                'attrs': {'question': 'question', 'display_name': 'display_name'}
            },
            # Two attributes (name, display_name): Prefer name
            {
                'usage_id': u'7',
                'preferred_attr': 'name',
                'attrs': {'name': 'name', 'display_name': 'display_name'}
            },
            # All attributes: Prefer question
            {
                'usage_id': u'8',
                'preferred_attr': 'question',
                'attrs': {'question': 'question', 'name': 'name', 'display_name': 'display_name'}
            },
        ]

    def test_build_course_tree_uses_preferred_attrs(self):
        """
        Check if `_build_course_tree` method uses preferred block
        attributes for `id` and `name` of each block.

        Each entry of the block tree returned by `_build_course_tree`
        is a dictionary that must contain an `id` key and a `name`
        key.

        - `id` must be set to the ID (usage_id or block_id)
          of the corresponding block.

        - `name` must be set to the value of one of the following attributes
           of the corresponding block:

          - question
          - name (question ID)
          - display_name (question title)
          - block ID

          Note that the attributes are listed in order of preference;
          i.e., if `block.question` has a meaningful value, that value
          should be used for `name` (irrespective of what the values
          of the other attributes might be).
        """
        block_tree = self.block._build_course_tree()

        def check_block(usage_id, expected_name):
            # - Does block_tree contain single entry whose `id` matches `usage_id` of block?
            matching_blocks = [block for block in block_tree if block['id'] == usage_id]
            self.assertEqual(len(matching_blocks), 1)
            # - Is `name` of that entry set to `expected_name`?
            matching_block = matching_blocks[0]
            self.assertEqual(matching_block['name'], expected_name)

        # Check size of block_tree
        num_blocks = len(self.block.children) + 1
        self.assertEqual(len(block_tree), num_blocks)

        # Check block_tree for root entry
        check_block(usage_id=self.block.scope_ids.usage_id, expected_name='All')

        # Check block_tree for children
        for child in self.block.children:
            usage_id = child.get('usage_id')
            attrs = child.get('attrs', {})
            if not attrs:
                expected_name = usage_id
            else:
                preferred_attr = child.get('preferred_attr')
                expected_name = attrs[preferred_attr]
            check_block(usage_id, expected_name)

    def test_build_course_tree_excludes_choice_blocks(self):
        """
        Check if `_build_course_tree` method excludes 'pb-choice' blocks.
        """
        # Pretend that all blocks in self.block.children are of type 'pb-choice:
        self.runtime_mock.id_reader = Mock()
        self.runtime_mock.id_reader.get_block_type.return_value = 'pb-choice'

        block_tree = self.block._build_course_tree()

        # Check size of block_tree: Should only include root block
        self.assertEqual(len(block_tree), 1)

    @ddt.data('pb-mcq', 'pb-rating', 'pb-answer')
    def test_build_course_tree_eligible_blocks(self, block_type):
        """
        Check if `_build_course_tree` method correctly marks MCQ, Rating,
        and Answer blocks as eligible.

        A block is eligible if its type is one of {'pb-mcq', 'pb-rating', 'pb-answer'}.
        """
        # Pretend that all blocks in self.block.children are eligible:
        self.runtime_mock.id_reader = Mock()
        self.runtime_mock.id_reader.get_block_type.return_value = block_type

        block_tree = self.block._build_course_tree()

        # Check size of block_tree: All blocks should be included
        num_blocks = len(self.block.children) + 1
        self.assertEqual(len(block_tree), num_blocks)

        # Check if all blocks are eligible:
        self.assertTrue(all(block['eligible'] for block in block_tree))

    @ddt.data(
        'problem-builder',
        'pb-table',
        'pb-column',
        'pb-answer-recap',
        'pb-mrq',
        'pb-message',
        'pb-tip',
        'pb-dashboard',
        'pb-data-export',
        'pb-instructor-tool',
    )
    def test_build_course_tree_ineligible_blocks(self, block_type):
        """
        Check if `_build_course_tree` method correctly marks blocks that
        aren't MCQ, Rating, or Answer blocks as ineligible.
        """
        # Pretend that none of the blocks in self.block.children are eligible:
        self.runtime_mock.id_reader = Mock()
        self.runtime_mock.id_reader.get_block_type.return_value = block_type

        block_tree = self.block._build_course_tree()

        # Check size of block_tree: All blocks should be included (they are not of type 'pb-choice')
        num_blocks = len(self.block.children) + 1
        self.assertEqual(len(block_tree), num_blocks)

        # Check if all blocks are ineligible:
        self.assertTrue(all(not block['eligible'] for block in block_tree))

    def test_build_course_tree_supports_new_style_keys(self):
        """
        Check if `_build_course_tree` method correctly handles new-style keys.

        To determine eligibility of a given block,
        `_build_course_tree` has to obtain the blocks's type. It uses
        `block.runtime.id_reader.get_block_type` to do this. It first
        tries to pass `block.scope_ids.def_id` as an argument.

        **If old-style keys are enabled, this will work. If new-style
        keys are enabled, this will fail with an AttributeError.**

        `_build_course_tree` should not let this error bubble up.
        Instead, it should catch the error and try again, this time
        passing `block.scope_ids.usage_id` to the method mentioned
        above (which will work if new-style keys are enabled).
        """
        # Pretend that new-style keys are enabled:
        self.block.scope_ids.def_id = Mock()
        self.block.scope_ids.def_id.block_type.side_effect = AttributeError()

        try:
            self.block._build_course_tree()
        except AttributeError:
            self.fail('student_view breaks if new-style keys are enabled.')

    def test_student_view_template_args(self):
        """
        Check if `student_view` calls rendering method of template loader
        with correct arguments.
        """
        block_choices = {
            'Multiple Choice Question': 'MCQBlock',
            'Rating Question': 'RatingBlock',
            'Long Answer': 'AnswerBlock',
        }
        flat_block_tree = ['block{}'.format(i) for i in range(10)]
        self.block._build_course_tree = Mock(return_value=flat_block_tree)

        with patch('problem_builder.instructor_tool.loader') as patched_loader:
            patched_loader.render_template.return_value = u''
            self.block.student_view()
            patched_loader.render_template.assert_called_once_with(
                'templates/html/instructor_tool.html',
                {'block_choices': block_choices, 'block_tree': flat_block_tree}
            )

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
