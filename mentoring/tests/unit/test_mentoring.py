import unittest
from mock import MagicMock, Mock, patch
from xblock.field_data import DictFieldData
from mentoring import MentoringBlock


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
