"""
Unit tests for DashboardVisualData
"""
from mentoring.dashboard_visual import DashboardVisualData
from mock import MagicMock, Mock
import unittest
from xblock.field_data import DictFieldData


class TestDashboardVisualData(unittest.TestCase):
    """
    Test DashboardVisualData with some mocked data
    """
    def test_construct_data(self):
        """
        Test parsing of data and creation of SVG filter data.
        """
        blocks = [
            {
                'display_name': 'Block 1',
                'mcqs': [],
                'has_average': True,
                'average': 0,
            },
            {
                'display_name': 'Block 2',
                'mcqs': [],
                'has_average': True,
                'average': 1.3,
            },
            {
                'display_name': 'Block 3',
                'mcqs': [],
                'has_average': True,
                'average': 30.8,
            },
        ]
        rules = {
            "images": [
                "step1.png",
                "step2.png",
                "step3.png",
            ],
            "background": "background.png",
            "overlay": "overlay.png",
            "colorRules": [
                {"if": "x < 1", "hueRotate": "20"},
                {"if": "x < 2", "hueRotate": "80", "blur": "1"},
                {"blur": "x / 2", "saturate": "0.4"}
            ],
            "width": "500",
            "height": "500"
        }
        data = DashboardVisualData(blocks, rules)
        self.assertEqual(len(data.layers), 5)
        self.assertEqual(data.layers[0]["url"], "background.png")
        self.assertEqual(data.layers[4]["url"], "overlay.png")
        self.assertEqual(data.width, 500)
        self.assertEqual(data.height, 500)
        # Check the three middle layers built from the average values:
        # Step 1, average is 0 - first colorRule should match
        self.assertEqual(data.layers[1]["url"], "step1.png")
        self.assertEqual(data.layers[1]["has_filter"], True)
        self.assertEqual(data.layers[1]["hueRotate"], 20)
        # Step 2, average is 1.3 - second colorRule should match
        self.assertEqual(data.layers[2]["url"], "step2.png")
        self.assertEqual(data.layers[2]["has_filter"], True)
        self.assertEqual(data.layers[2]["hueRotate"], 80)
        self.assertEqual(data.layers[2]["blur"], 1)
        # Step 3, average is 30.8 - final colorRule should match
        self.assertEqual(data.layers[3]["url"], "step3.png")
        self.assertEqual(data.layers[3]["has_filter"], True)
        self.assertEqual(data.layers[3]["blur"], 30.8/2)
        self.assertEqual(data.layers[3]["saturate"], 0.4)
