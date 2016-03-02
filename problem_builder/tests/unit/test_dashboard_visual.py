"""
Unit tests for DashboardVisualData
"""
import unittest

from problem_builder.dashboard_visual import DashboardVisualData


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
            "width": "500",
            "height": "500"
        }

        def color_for_value(value):
            """ Mock color_for_value """
            return "red" if value > 1 else None

        data = DashboardVisualData(blocks, rules, color_for_value, "Visual Repr", "Description here")
        self.assertEqual(len(data.layers), 5)
        self.assertEqual(data.layers[0]["url"], "background.png")
        self.assertEqual(data.layers[4]["url"], "overlay.png")
        self.assertEqual(data.width, 500)
        self.assertEqual(data.height, 500)
        # Check the three middle layers built from the average values:
        self.assertEqual(data.layers[1]["url"], "step1.png")
        self.assertEqual(data.layers[1].get("color"), None)

        self.assertEqual(data.layers[2]["url"], "step2.png")
        self.assertEqual(data.layers[2]["color"], "red")

        self.assertEqual(data.layers[3]["url"], "step3.png")
        self.assertEqual(data.layers[3]["color"], "red")
