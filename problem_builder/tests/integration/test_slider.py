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

# Imports ###########################################################

from .base_test import (GetChoices, MentoringAssessmentBaseTest,
                        ProblemBuilderBaseTest)

# Classes ###########################################################


class SliderBlockTestMixins:
    """ Mixins for testing slider blocks. Assumes only one slider block is on the page. """

    def get_slider_value(self):
        return int(self.browser.execute_script("return $('.pb-slider-range').val()"))

    def set_slider_value(self, val):
        self.browser.execute_script("$('.pb-slider-range').val(arguments[0]).change()", val)


class SliderBlockTest(SliderBlockTestMixins, ProblemBuilderBaseTest):
    """
    Tests for the SliderBlock inside a normal Problem Builder block.
    """
    def test_simple_flow(self):
        """ Test a regular Problem Builder block containing one slider """
        pb_wrapper = self.load_scenario("slider_problem.xml", {"include_mcq": False})
        self.wait_for_init()
        # The initial value should be 50 and submit should be enabled since 50 is a valid value:
        self.assertEqual(self.get_slider_value(), 50)
        self.expect_checkmark_visible(False)
        self.expect_submit_enabled(True)
        # Set the value to 75:
        self.set_slider_value(75)
        self.assertEqual(self.get_slider_value(), 75)
        self.click_submit(pb_wrapper)
        # Now, we expect submit to be disabled and the checkmark to be visible:
        self.expect_checkmark_visible(True)
        self.expect_submit_enabled(False)
        # Now change the value, and the button/checkmark should reset:
        self.set_slider_value(45)
        self.expect_checkmark_visible(False)
        self.expect_submit_enabled(True)
        # Now reload the page:
        pb_wrapper = self.reload_page()
        self.wait_for_init()
        # Now the initial value should be 75 and submit should be disabled (to discourage submitting the same answer):
        self.assertEqual(self.get_slider_value(), 75)
        self.wait_until_visible(self.checkmark)
        self.expect_checkmark_visible(True)
        self.expect_submit_enabled(False)

    def test_simple_flow_with_peer(self):
        """ Test a regular Problem Builder block containing one slider and an MCQ """
        pb_wrapper = self.load_scenario("slider_problem.xml", {"include_mcq": True})
        self.wait_for_init()
        # The initial value should be 50 and submit should be disabled until an MCQ choice is selected
        self.assertEqual(self.get_slider_value(), 50)
        self.expect_checkmark_visible(False)
        self.expect_submit_enabled(False)
        # Set the value to 15:
        self.set_slider_value(15)
        self.assertEqual(self.get_slider_value(), 15)
        self.expect_submit_enabled(False)
        # Choose a choice:
        GetChoices(pb_wrapper).select('Yes')
        self.expect_submit_enabled(True)
        self.click_submit(pb_wrapper)
        # Now, we expect submit to be disabled and the checkmark to be visible:
        self.expect_checkmark_visible(True)
        self.expect_submit_enabled(False)
        # Now change the value, and the button/checkmark should reset:
        self.set_slider_value(20)
        self.expect_checkmark_visible(False)
        self.expect_submit_enabled(True)


class SliderStepBlockTest(SliderBlockTestMixins, MentoringAssessmentBaseTest):
    """
    Tests for the SliderBlock inside a Step Builder block.
    """

    def test_step_with_slider(self):
        """ Test a regular Step Builder block containing one slider and an MCQ """
        step_builder, controls = self.load_assessment_scenario("slider_step.xml")
        self.wait_for_init()
        self.assertEqual(self.get_slider_value(), 50)

        # Check step 1 (the slider step):
        question = self.expect_question_visible(1, step_builder, question_text="Information Reliability")
        self.assertIn("How reliable is this information?", question.text)
        self.assertIn("Select a value from 0% to 100%", question.text)  # Screen reader explanation
        self.assertTrue(controls.submit.is_enabled())
        self.assert_hidden(controls.try_again)

        self.set_slider_value(0)
        controls.submit.click()
        self.do_submit_wait(controls, last=False)
        self.wait_until_clickable(controls.next_question)
        controls.next_question.click()

        # Submit step 2:
        question = self.expect_question_visible(2, step_builder)
        GetChoices(question).select("Yes")
        controls.submit.click()
        self.do_submit_wait(controls, last=True)
        self.wait_until_clickable(controls.review)

        controls.review.click()
        self.wait_until_visible(controls.try_again)
        # You can't get a slider question wrong, but it does count as one correct point by default:
        self.assertIn("You answered 2 questions correctly", step_builder.text)
