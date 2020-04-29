import unittest

import ddt
from unittest.mock import Mock
from xblock.field_data import DictFieldData

from problem_builder.swipe import SwipeBlock


@ddt.ddt
class TestSwipeBlock(unittest.TestCase):
    def test_student_view_data(self):
        """
        Ensure that all expected fields are always returned with
        appropriate values.
        """
        runtime = Mock(replace_urls=lambda url: '"{}"'.format(url))
        block = SwipeBlock(runtime, DictFieldData({"display_name": "Test"}), Mock())

        self.assertEqual(block.student_view_data()['correct'], False)
