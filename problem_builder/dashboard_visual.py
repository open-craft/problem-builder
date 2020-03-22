# -*- coding: utf-8 -*-
#
# Copyright (c) 2014-2015 Harvard, edX & OpenCraft
#
# This software's license gives you freedom; you can copy, convey,
# propagate, redistribute and/or modify this program under the terms of
# the GNU Affero General Public License (AGPL) as published by the Free
# Software Foundation (FSF), either version 3 of the License, or (at your
# option) any later version of the AGPL published by the FSF.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program in a file in the toplevel directory called
# "AGPLv3".  If not, see <http://www.gnu.org/licenses/>.
#
"""
Visual Representation of Dashboard State.

Consists of a series of images, layered on top of each other, where the appearance of each layer
can be tied to the average value of the student's response to a particular Problem Builder
block.

For example, each layer can have its color turn green if the student's average value on MCQs in
a specific Problem Builder block was at least 3.
"""


class DashboardVisualData:
    """
    Data about the visual representation of a dashboard.
    """
    def __init__(self, blocks, rules, color_for_value, title, desc):
        """
        Construct the data required for the optional visual representation of the dashboard.

        Data format accepted for rules is like:
        {
            "images": [
                "/static/step1.png",
                "/static/step2.png",
                "/static/step3.png",
                "/static/step4.png",
                "/static/step5.png",
                "/static/step6.png",
                "/static/step7.png"
            ],
            "background": "/static/background.png",
            "overlay": "/static/overlay.png",
            "width": "500",
            "height": "500"
        }

        color_for_value is a method that, given a value, returns a color string or None
        """
        # Images is a list of images, one per PB block, in the same order as 'blocks'
        # All images are rendered layered on top of each other, and can be hidden,
        # shown, colorized, faded, etc. based on the average answer value for that PB block.
        images = rules.get("images", [])
        # Overlay is an optional images drawn on top, with no effects applied
        overlay = rules.get("overlay")
        # Background is an optional images drawn on the bottom, with no effects applied
        background = rules.get("background")
        # Width and height of the image:
        self.width = int(rules.get("width", 400))
        self.height = int(rules.get("height", 400))
        # A unique ID used by the HTML template:
        self.unique_id = id(self)
        # Alternate dsescription for screen reader users:
        self.title = title
        self.desc = desc

        self.layers = []
        if background:
            self.layers.append({"url": background})
        for idx, block in enumerate(blocks):
            if not block.get("has_average"):
                continue  # We only use blocks with numeric averages for the visual representation
            # Now we build the 'layer_data' information to pass on to the template:
            try:
                layer_data = {"url": images[idx], "id": "layer{}".format(idx)}
            except IndexError:
                break

            # Check if a color rule applies:
            layer_data["color"] = color_for_value(block["average"])
            self.layers.append(layer_data)

        if overlay:
            self.layers.append({"url": overlay})
