import unittest
import ddt
from mock import MagicMock, Mock, patch
from xblock.field_data import DictFieldData
from problem_builder import MentoringBlock, MentoringMessageBlock, MCQBlock
from problem_builder.mentoring import _default_theme_config


@ddt.ddt
class TestMentoringBlock(unittest.TestCase):
    def test_sends_progress_event_when_rendered_student_view_with_display_submit_false(self):
        block = MentoringBlock(MagicMock(), DictFieldData({
            'display_submit': False
        }), Mock())

        with patch.object(block, 'runtime') as patched_runtime:
            patched_runtime.publish = Mock()

            block.student_view(context={})

            patched_runtime.publish.assert_called_once_with(block, 'progress', {})

    def test_does_not_send_progress_event_when_rendered_student_view_with_display_submit_true(self):
        block = MentoringBlock(MagicMock(), DictFieldData({
            'display_submit': True
        }), Mock())

        with patch.object(block, 'runtime') as patched_runtime:
            patched_runtime.publish = Mock()

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
            patched_runtime.service().ugettext = lambda str: str
            patched_runtime.get_block = lambda block_id: None
            patched_runtime.load_block_type = lambda block_id: Mock

            fragment = block.student_view(context={})

            self.assertIn('Unable to load child component', fragment.content)


@ddt.ddt
class TestMentoringBlockTheming(unittest.TestCase):
    def setUp(self):
        self.service_mock = Mock()
        self.runtime_mock = Mock()
        self.runtime_mock.service = Mock(return_value=self.service_mock)
        self.block = MentoringBlock(self.runtime_mock, DictFieldData({}), Mock())

    def test_theme_uses_default_theme_if_settings_service_is_not_available(self):
        self.runtime_mock.service = Mock(return_value=None)
        self.assertEqual(self.block.get_theme(), _default_theme_config)

    def test_theme_uses_default_theme_if_no_theme_is_set(self):
        self.service_mock.get_settings_bucket = Mock(return_value=None)
        self.assertEqual(self.block.get_theme(), _default_theme_config)
        self.service_mock.get_settings_bucket.assert_called_once_with(self.block)

    @ddt.data(123, object())
    def test_theme_raises_if_theme_object_is_not_iterable(self, theme_config):
        self.service_mock.get_settings_bucket = Mock(return_value=theme_config)
        with self.assertRaises(TypeError):
            self.block.get_theme()
        self.service_mock.get_settings_bucket.assert_called_once_with(self.block)

    @ddt.data(
        {}, {'mass': 123}, {'spin': {}}, {'parity': "1"}
    )
    def test_theme_uses_default_theme_if_no_mentoring_theme_is_set_up(self, theme_config):
        self.service_mock.get_settings_bucket = Mock(return_value=theme_config)
        self.assertEqual(self.block.get_theme(), _default_theme_config)
        self.service_mock.get_settings_bucket.assert_called_once_with(self.block)

    @ddt.data(
        {MentoringBlock.theme_key: 123},
        {MentoringBlock.theme_key: [1, 2, 3]},
        {MentoringBlock.theme_key: {'package': 'qwerty', 'locations': ['something_else.css']}},
    )
    def test_theme_correctly_returns_configured_theme(self, theme_config):
        self.service_mock.get_settings_bucket = Mock(return_value=theme_config)
        self.assertEqual(self.block.get_theme(), theme_config[MentoringBlock.theme_key])

    def test_theme_files_are_loaded_from_correct_package(self):
        fragment = MagicMock()
        package_name = 'some_package'
        theme_config = {MentoringBlock.theme_key: {'package': package_name, 'locations': ['lms.css']}}
        self.service_mock.get_settings_bucket = Mock(return_value=theme_config)
        with patch("problem_builder.mentoring.ResourceLoader") as patched_resource_loader:
            self.block.include_theme_files(fragment)
            patched_resource_loader.assert_called_with(package_name)

    @ddt.data(
        ('problem_builder', ['public/themes/lms.css']),
        ('problem_builder', ['public/themes/lms.css', 'public/themes/lms.part2.css']),
        ('my_app.my_rules', ['typography.css', 'icons.css']),
    )
    @ddt.unpack
    def test_theme_files_are_added_to_fragment(self, package_name, locations):
        fragment = MagicMock()
        theme_config = {MentoringBlock.theme_key: {'package': package_name, 'locations': locations}}
        self.service_mock.get_settings_bucket = Mock(return_value=theme_config)
        with patch("problem_builder.mentoring.ResourceLoader.load_unicode") as patched_load_unicode:
            self.block.include_theme_files(fragment)
            for location in locations:
                patched_load_unicode.assert_any_call(location)

            self.assertEqual(patched_load_unicode.call_count, len(locations))

    def test_student_view_calls_include_theme_files(self):
        with patch.object(self.block, 'include_theme_files') as patched_include_theme_files:
            fragment = self.block.student_view({})
            patched_include_theme_files.assert_called_with(fragment)

    def test_author_preview_view_calls_include_theme_files(self):
        with patch.object(self.block, 'include_theme_files') as patched_include_theme_files:
            fragment = self.block.author_preview_view({})
            patched_include_theme_files.assert_called_with(fragment)


class TestMentoringBlockJumpToIds(unittest.TestCase):
    def setUp(self):
        self.service_mock = Mock()
        self.runtime_mock = Mock()
        self.runtime_mock.service = Mock(return_value=self.service_mock)
        self.block = MentoringBlock(self.runtime_mock, DictFieldData({'mode': 'assessment'}), Mock())
        self.block.children = ['dummy_id']
        self.message_block = MentoringMessageBlock(
            self.runtime_mock, DictFieldData({'type': 'bogus', 'content': 'test'}), Mock()
        )
        self.block.runtime.replace_jump_to_id_urls = lambda x: x.replace('test', 'replaced-url')

    def test_get_message_content(self):
        with patch('problem_builder.mentoring.child_isinstance') as mock_child_isinstance:
            mock_child_isinstance.return_value = True
            self.runtime_mock.get_block = Mock()
            self.runtime_mock.get_block.return_value = self.message_block
            self.assertEqual(self.block.get_message_content('bogus'), 'replaced-url')

    def test_get_tip_content(self):
        self.mcq_block = MCQBlock(self.runtime_mock, DictFieldData({'name': 'test_mcq'}), Mock())
        self.mcq_block.get_review_tip = Mock()
        self.mcq_block.get_review_tip.return_value = self.message_block.content
        self.block.step_ids = []
        self.block.steps = [self.mcq_block]
        self.block.student_results = {'test_mcq': {'status': 'incorrect'}}
        self.assertEqual(self.block.review_tips, ['replaced-url'])
