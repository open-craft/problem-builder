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
import re
import mock
import ddt
from selenium.common.exceptions import NoSuchElementException
from .base_test import MentoringBaseTest, MentoringAssessmentBaseTest, GetChoices


class MentoringTest(MentoringBaseTest):
    def test_display_submit_false_does_not_display_submit(self):
        mentoring = self.go_to_page('No Display Submit')
        with self.assertRaises(NoSuchElementException):
            mentoring.find_element_by_css_selector('.submit input.input-main')


def _get_mentoring_theme_settings(theme):
    return {
        'package': 'problem_builder',
        'locations': ['public/themes/{}.css'.format(theme)]
    }


@ddt.ddt
class MentoringThemeTest(MentoringAssessmentBaseTest):
    def rgb_to_hex(self, rgb):
        r, g, b = map(int, re.search(r'rgba?\((\d+),\s*(\d+),\s*(\d+)', rgb).groups())
        return '#%02x%02x%02x' % (r, g, b)

    def assert_status_icon_color(self, color):
        mentoring, controls = self.go_to_assessment('Theme 1')
        question = self.expect_question_visible(0, mentoring)
        choice_name = "Maybe not"

        choices = GetChoices(question)
        expected_state = {"Yes": False, "Maybe not": False, "I don't understand": False}
        self.assertEquals(choices.state, expected_state)

        choices.select(choice_name)
        expected_state[choice_name] = True
        self.assertEquals(choices.state, expected_state)

        controls.submit.click()
        self.wait_until_disabled(controls.submit)

        answer_result = mentoring.find_element_by_css_selector(".assessment-checkmark")
        self.assertEqual(self.rgb_to_hex(answer_result.value_of_css_property("color")), color)

    @ddt.unpack
    @ddt.data(
        ('lms', "#c1373f"),
        ('apros', "#ff0000")
    )
    def test_lms_theme_applied(self, theme, expected_color):
        with mock.patch("problem_builder.MentoringBlock.get_theme") as patched_theme:
            patched_theme.return_value = _get_mentoring_theme_settings(theme)
            self.assert_status_icon_color(expected_color)
