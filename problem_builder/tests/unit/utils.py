"""
Helper methods for testing Problem Builder / Step Builder blocks
"""
import json
from datetime import date, datetime
from unittest.mock import MagicMock, Mock, patch

from xblock.field_data import DictFieldData


class ScoresTestMixin:
    """
    Mixin for tests that involve scores (grades)
    """
    def assert_produces_scores(self, block):
        """
        Test that the given XBlock instance meets the requirements of being able to report
        scores to the edX LMS, and have them appear on the student's progress page.
        """
        self.assertTrue(block.has_score)
        self.assertTrue(type(block).has_score)
        self.assertEqual(block.weight, 1.0)  # Default weight should be 1
        self.assertIsInstance(block.max_score(), (int, float))


class BlockWithChildrenTestMixin:
    """
    Mixin for tests targeting blocks that contain nested child blocks.
    """

    ALLOWED_NESTED_BLOCKS = [
        'pb-answer',
        'pb-mcq',
        'pb-rating',
        'pb-mrq',
        'pb-completion',
        'html',
        'pb-answer-recap',
        'pb-table',
        'sb-plot',
        'pb-slider',
    ]

    ADDITIONAL_BLOCKS = [
        'video',
        'imagemodal',
        'ooyala-player',
    ]

    def get_allowed_blocks(self, block):
        """
        Return list of categories corresponding to child blocks allowed for `block`.
        """
        return [
            getattr(allowed_block, 'category', getattr(allowed_block, 'CATEGORY', None))
            for allowed_block in block.allowed_nested_blocks
        ]

    def assert_allowed_nested_blocks(self, block, message_blocks=[]):
        self.assertEqual(
            self.get_allowed_blocks(block),
            self.ALLOWED_NESTED_BLOCKS + message_blocks
        )
        from sys import modules
        xmodule_mock = Mock()
        fake_modules = {
            'xmodule': xmodule_mock,
            'xmodule.video_module': xmodule_mock.video_module,
            'xmodule.video_module.video_module': xmodule_mock.video_module.video_module,
            'imagemodal': Mock(),
            'ooyala_player.ooyala_player': Mock(),
        }
        with patch.dict(modules, fake_modules):
            self.assertEqual(
                self.get_allowed_blocks(block),
                self.ALLOWED_NESTED_BLOCKS + self.ADDITIONAL_BLOCKS + message_blocks
            )


def instantiate_block(cls, fields=None):
    """
    Instantiate the given XBlock in a mock runtime.
    """
    fields = fields or {}
    children = fields.pop('children', {})
    field_data = DictFieldData(fields or {})
    block = cls(
        runtime=Mock(),
        field_data=field_data,
        scope_ids=MagicMock()
    )
    block.children = children
    block.runtime.get_block = lambda child_id: children[child_id]
    return block


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (datetime, date)):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)
