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
Test that the various title/display_name options for Answer and MCQ/MRQ/Ratings work.
"""

from unittest.mock import patch

# Imports ###########################################################
import ddt
from xblockutils.base_test import SeleniumXBlockTest

# Classes ###########################################################


@ddt.ddt
class TitleTest(SeleniumXBlockTest):
    """
    Test the various display_name/show_title options for Problem Builder
    """

    @ddt.data(
        ('<problem-builder show_title="false"><pb-answer name="a"/></problem-builder>', None),
        ('<problem-builder><pb-answer name="a"/></problem-builder>', "Problem Builder"),
        ('<problem-builder mode="assessment"><pb-answer name="a"/></problem-builder>', "Problem Builder"),
        ('<problem-builder display_name="A Question"><pb-answer name="a"/></problem-builder>', "A Question"),
        ('<problem-builder display_name="A Question" show_title="false"><pb-answer name="a"/></problem-builder>', None),
    )
    @ddt.unpack
    def test_title(self, xml, expected_title):
        self.set_scenario_xml(xml)
        pb_element = self.go_to_view()
        if expected_title is not None:
            h3 = pb_element.find_element_by_css_selector('h3')
            self.assertEqual(h3.text, expected_title)
        else:
            # No <h3> element should be present:
            all_h3s = pb_element.find_elements_by_css_selector('h3')
            self.assertEqual(len(all_h3s), 0)


class StepTitlesTest(SeleniumXBlockTest):
    """
    Test that the various title/display_name options for Answer and MCQ/MRQ/Ratings work.
    """

    test_parameters = (
        # display_name, show_title?, expected_title:  (None means default value)
        ("Custom Title", None,  "Custom Title",),
        ("Custom Title", True,  "Custom Title",),
        ("Custom Title", False, None),
        ("",             None,  "Question"),
        ("",             True,  "Question"),
        ("",             False, None),
    )

    mcq_template = """
        <problem-builder>
            <pb-mcq name="mcq_1_1" question="Who was your favorite character?"
              correct_choices="[gaius,adama,starbuck,roslin,six,lee]"
              {display_name_attr} {show_title_attr}
            >
                <pb-choice value="gaius">Gaius Baltar</pb-choice>
                <pb-choice value="adama">Admiral William Adama</pb-choice>
                <pb-choice value="starbuck">Starbuck</pb-choice>
                <pb-choice value="roslin">Laura Roslin</pb-choice>
                <pb-choice value="six">Number Six</pb-choice>
                <pb-choice value="lee">Lee Adama</pb-choice>
            </pb-mcq>
        </problem-builder>
    """

    mrq_template = """
        <problem-builder>
            <pb-mrq name="mrq_1_1" question="What makes a great MRQ?"
              ignored_choices="[1,2,3]"
              {display_name_attr} {show_title_attr}
            >
                <pb-choice value="1">Lots of choices</pb-choice>
                <pb-choice value="2">Funny choices</pb-choice>
                <pb-choice value="3">Not sure</pb-choice>
            </pb-mrq>
        </problem-builder>
    """

    rating_template = """
        <problem-builder>
            <pb-rating name="rating_1_1" question="How do you rate Battlestar Galactica?"
              correct_choices="[5,6]"
              {display_name_attr} {show_title_attr}
            >
                <pb-choice value="6">More than 5 stars</pb-choice>
            </pb-rating>
        </problem-builder>
    """

    long_answer_template = """
        <problem-builder>
            <pb-answer name="answer_1_1" question="What did you think of the ending?"
              {display_name_attr} {show_title_attr} />
        </problem-builder>
    """

    def setUp(self):
        super().setUp()
        # Disable asides for this test since the acid aside seems to cause Database errors
        # When we test multiple scenarios in one test method.
        patcher = patch(
            'workbench.runtime.WorkbenchRuntime.applicable_aside_types',
            lambda self, block: [], create=True
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_all_the_things(self):
        """ Test various permutations of our problem-builder components and title options. """
        # We use a loop within the test rather than DDT, because this is WAY faster
        # since we can bypass the Selenium set-up and teardown
        for display_name, show_title, expected_title in self.test_parameters:
            for qtype in ("mcq", "mrq", "rating", "long_answer"):
                template = getattr(self, qtype + "_template")
                xml = template.format(
                    display_name_attr=f'display_name="{display_name}"' if display_name is not None else "",
                    show_title_attr=f'show_title="{show_title}"' if show_title is not None else "",
                )
                self.set_scenario_xml(xml)
                pb_element = self.go_to_view()
                if expected_title:
                    h4 = pb_element.find_element_by_css_selector('h4')
                    self.assertEqual(h4.text, expected_title)
                else:
                    # No <h4> element should be present:
                    all_h4s = pb_element.find_elements_by_css_selector('h4')
                    self.assertEqual(len(all_h4s), 0)
