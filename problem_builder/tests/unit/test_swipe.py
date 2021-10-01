import unittest
from unittest.mock import Mock

import ddt
from xblock.field_data import DictFieldData

from problem_builder.swipe import SwipeBlock


@ddt.ddt
class TestSwipeBlock(unittest.TestCase):
    def test_student_view_data(self):
        """
        Ensure that all expected fields are always returned with
        appropriate values.
        """
        runtime = Mock(replace_urls=lambda url: f'"{url}"')
        block = SwipeBlock(runtime, DictFieldData({"display_name": "Test"}), Mock())

        self.assertEqual(block.student_view_data()['correct'], False)
