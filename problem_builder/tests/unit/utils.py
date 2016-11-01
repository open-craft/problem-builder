"""
Helper methods for testing Problem Builder / Step Builder blocks
"""
from mock import MagicMock, Mock
from xblock.field_data import DictFieldData


class ScoresTestMixin(object):
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
