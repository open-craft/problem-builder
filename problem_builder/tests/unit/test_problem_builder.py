import unittest
from random import random
from unittest.mock import MagicMock, Mock, PropertyMock, patch

import ddt
from xblock.field_data import DictFieldData
from xblock.runtime import NullI18nService

from problem_builder.answer import AnswerRecapBlock
from problem_builder.mcq import MCQBlock
from problem_builder.mentoring import (MentoringBlock, MentoringMessageBlock,
                                       _default_options_config)
from problem_builder.mrq import MRQBlock

from .utils import BlockWithChildrenTestMixin


@ddt.ddt
class TestMRQBlock(BlockWithChildrenTestMixin, unittest.TestCase):
    def test_student_view_data(self):
        """
        Ensure that all expected fields are always returned.
        """
        block = MRQBlock(Mock(), DictFieldData({}), Mock())

        self.assertEqual(
            sorted(block.student_view_data().keys()),
            sorted([
                'hide_results', 'tips', 'block_id', 'display_name',
                'weight', 'title', 'question', 'message', 'type', 'id', 'choices'
            ])
        )


@ddt.ddt
class TestAnswerRecapBlock(BlockWithChildrenTestMixin, unittest.TestCase):
    def test_student_view_data(self):
        """
        Ensure that all expected fields are always returned.
        """
        block = AnswerRecapBlock(Mock(), DictFieldData({}), Mock())

        self.assertEqual(
            sorted(block.student_view_data().keys()),
            sorted([
                'block_id', 'display_name', 'type', 'id', 'name', 'description'
            ])
        )


@ddt.ddt
class TestMentoringBlock(BlockWithChildrenTestMixin, unittest.TestCase):
    def test_sends_progress_event_when_rendered_student_view_with_display_submit_false(self):
        block = MentoringBlock(MagicMock(), DictFieldData({
            'display_submit': False
        }), Mock())

        with patch.object(block, 'runtime') as patched_runtime:
            patched_runtime.publish = Mock()
            patched_runtime.service = lambda _, service: NullI18nService() if service == 'i18n' else MagicMock()

            block.student_view(context={})

            patched_runtime.publish.assert_called_once_with(block, 'progress', {})

    def test_does_not_send_progress_event_when_rendered_student_view_with_display_submit_true(self):
        block = MentoringBlock(MagicMock(), DictFieldData({
            'display_submit': True
        }), Mock())

        with patch.object(block, 'runtime') as patched_runtime:
            patched_runtime.publish = Mock()
            patched_runtime.service = lambda _, service: NullI18nService() if service == 'i18n' else MagicMock()

            block.student_view(context={})

            self.assertFalse(patched_runtime.publish.called)

    @ddt.data(True, False)
    def test_get_content_titles(self, has_title_set):
        """
        Test that we don't send a title to the LMS for the sequential's tooltips when no title
        is set
        """
        if has_title_set:
            data = {'display_name': 'Custom Title'}
            expected = ['Custom Title']
        else:
            data = {}
            expected = []
        block = MentoringBlock(MagicMock(), DictFieldData(data), Mock())
        self.assertEqual(block.get_content_titles(), expected)

    def test_does_not_crash_when_get_child_is_broken(self):
        block = MentoringBlock(MagicMock(), DictFieldData({
            'children': ['invalid_id'],
        }), Mock())

        with patch.object(block, 'runtime') as patched_runtime:
            patched_runtime.publish = Mock()
            patched_runtime.service = lambda _, service: NullI18nService() if service == 'i18n' else MagicMock()
            patched_runtime.get_block = lambda block_id: None
            patched_runtime.load_block_type = lambda block_id: Mock

            fragment = block.student_view(context={})

            self.assertIn('Unable to load child component', fragment.content)

    @ddt.data(
        (True, True, True),
        (True, False, False),
        (False, False, True),
        (False, False, True),
    )
    @ddt.unpack
    def test_correctly_decides_to_show_or_hide_feedback_message(
            self, pb_hide_feedback_if_attempts_remain, max_attempts_reached, expected_show_message
    ):
        block = MentoringBlock(Mock(), DictFieldData({
            'student_results': ['must', 'be', 'non-empty'],
        }), Mock())
        block.get_option = Mock(return_value=pb_hide_feedback_if_attempts_remain)
        with patch(
                'problem_builder.mentoring.MentoringBlock.max_attempts_reached', new_callable=PropertyMock
        ) as patched_max_attempts_reached:
            patched_max_attempts_reached.return_value = max_attempts_reached
            _, _, show_message = block._get_standard_results()
            self.assertEqual(show_message, expected_show_message)

    def test_allowed_nested_blocks(self):
        block = MentoringBlock(Mock(), DictFieldData({}), Mock())
        self.assert_allowed_nested_blocks(block, message_blocks=[
                'pb-message',  # Message type: "completed"
                'pb-message',  # Message type: "incomplete"
                'pb-message',  # Message type: "max_attempts_reached"
            ]
        )

    def test_student_view_data(self):
        def get_mock_components():
            child_a = Mock(spec=['student_view_data'])
            child_a.block_id = 'child_a'
            child_a.category = 'text'
            child_a.student_view_data.return_value = 'child_a_json'
            child_b = Mock(spec=[])
            child_b.block_id = 'child_b'
            child_b.category = 'html'
            return [child_a, child_b]
        shared_data = {
            'max_attempts': 3,
            'extended_feedback': True,
            'feedback_label': 'Feedback label',
        }
        children = get_mock_components()
        children_by_id = {child.block_id: child for child in children}
        display_name = "I'm problem builder"
        block_data = {'display_name': display_name, 'children': children}
        block_data.update(shared_data)
        block = MentoringBlock(Mock(usage_id=1), DictFieldData(block_data), Mock(usage_id=1))
        block.runtime = Mock(
            get_block=lambda block: children_by_id[block.block_id],
            load_block_type=lambda block: Mock,
            id_reader=Mock(get_definition_id=lambda block: block, get_block_type=lambda block: block),
        )
        expected = {
            'block_id': '1',
            'display_name': display_name,
            'components': ['child_a_json'],
            'messages': {
                'completed': None,
                'incomplete': None,
                'max_attempts_reached': None,
            }
        }
        expected.update(shared_data)
        self.assertEqual(block.student_view_data(), expected)


@ddt.ddt
class TestMentoringBlockOptions(unittest.TestCase):
    def setUp(self):
        self.service_mock = Mock()
        self.runtime_mock = Mock()
        self.runtime_mock.service = Mock(return_value=self.service_mock)
        self.block = MentoringBlock(self.runtime_mock, DictFieldData({}), Mock())

    def test_get_options_returns_default_if_settings_service_is_not_available(self):
        self.runtime_mock.service = Mock(return_value=None)
        self.assertEqual(self.block.get_options(), _default_options_config)

    def test_get_options_returns_default_if_xblock_settings_not_customized(self):
        self.block.get_xblock_settings = Mock(return_value=None)
        self.assertEqual(self.block.get_options(), _default_options_config)
        self.block.get_xblock_settings.assert_called_once_with(default={})

    @ddt.data(
        {}, {'mass': 123}, {'spin': {}}, {'parity': "1"}
    )
    def test_get_options_returns_default_if_options_not_customized(self, xblock_settings):
        self.block.get_xblock_settings = Mock(return_value=xblock_settings)
        self.assertEqual(self.block.get_options(), _default_options_config)
        self.block.get_xblock_settings.assert_called_once_with(default={})

    @ddt.data(
        {MentoringBlock.options_key: 123},
        {MentoringBlock.options_key: [1, 2, 3]},
        {MentoringBlock.options_key: {'pb_mcq_hide_previous_answer': False}},
     )
    def test_get_options_correctly_returns_customized_options(self, xblock_settings):
        self.block.get_xblock_settings = Mock(return_value=xblock_settings)
        self.assertEqual(self.block.get_options(), xblock_settings[MentoringBlock.options_key])
        self.block.get_xblock_settings.assert_called_once_with(default={})

    def test_get_option(self):
        random_key, random_value = random(), random()
        with patch.object(self.block, 'get_options') as patched_get_options:
            # Happy path: Customizations contain expected key
            patched_get_options.return_value = {random_key: random_value}
            option = self.block.get_option(random_key)
            patched_get_options.assert_called_once_with()
            self.assertEqual(option, random_value)
        with patch.object(self.block, 'get_options') as patched_get_options:
            # Sad path: Customizations do not contain expected key
            patched_get_options.return_value = {}
            option = self.block.get_option(random_key)
            patched_get_options.assert_called_once_with()
            self.assertEqual(option, None)

    def test_student_view_calls_get_option(self):
        random_key, random_value = random(), random()
        self.block.get_xblock_settings = Mock(return_value={})
        with patch.object(self.block, 'get_option') as patched_get_option:
            self.runtime_mock.service.return_value = {
                random_key: random_value,
            }
            self.block.student_view({})
            patched_get_option.assert_any_call('pb_mcq_hide_previous_answer')
            patched_get_option.assert_any_call('pb_hide_feedback_if_attempts_remain')

    def test_get_standard_results_calls_get_option(self):
        with patch.object(self.block, 'get_option') as patched_get_option:
            self.block._get_standard_results()
            patched_get_option.assert_called_with('pb_hide_feedback_if_attempts_remain')


class TestMentoringBlockJumpToIds(unittest.TestCase):
    def setUp(self):
        self.service_mock = Mock()
        self.runtime_mock = Mock()
        self.runtime_mock.service = Mock(return_value=self.service_mock)
        self.block = MentoringBlock(self.runtime_mock, DictFieldData({}), Mock())
        self.block.children = ['dummy_id']
        self.message_block = MentoringMessageBlock(
            self.runtime_mock, DictFieldData({'type': 'bogus', 'content': 'test'}), Mock()
        )
        self.block.runtime.replace_jump_to_id_urls = lambda x: x.replace('test', 'replaced-url')

    def test_get_message_content(self):
        with patch('problem_builder.mixins.child_isinstance') as mock_child_isinstance:
            mock_child_isinstance.return_value = True
            self.runtime_mock.get_block = Mock()
            self.runtime_mock.get_block.return_value = self.message_block
            self.assertEqual(self.block.get_message_content('bogus'), 'replaced-url')

    def test_get_tip_content(self):
        self.mcq_block = MCQBlock(self.runtime_mock, DictFieldData({'name': 'test_mcq'}), Mock())
        self.mcq_block.get_review_tip = Mock()
        self.mcq_block.get_review_tip.return_value = self.message_block.content
        self.assertEqual(self.block.review_tips, [])

    def test_get_tip_content_no_tips(self):
        self.mcq_block = MCQBlock(self.runtime_mock, DictFieldData({'name': 'test_mcq'}), Mock())
        self.mcq_block.get_review_tip = Mock()
        # If there are no review tips, get_review_tip will return None;
        # simulate this situation here:
        self.mcq_block.get_review_tip.return_value = None
        self.block.step_ids = []
        self.block.steps = [self.mcq_block]
        self.block.student_results = {'test_mcq': {'status': 'incorrect'}}
        try:
            review_tips = self.block.review_tips
        except TypeError:
            self.fail('Trying to replace jump_to_id URLs in non-existent review tips.')
        else:
            self.assertEqual(review_tips, [])
