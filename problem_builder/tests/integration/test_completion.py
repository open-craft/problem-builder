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
import time

from .base_test import (GetChoices, MentoringAssessmentBaseTest,
                        ProblemBuilderBaseTest)

# Classes ###########################################################


class CompletionBlockTestMixin:
    """
    Mixin for testing completion blocks.
    """

    @property
    def checkmarks(self):
        return self.browser.find_elements_by_css_selector('.submit-result')

    @property
    def completion_checkbox(self):
        return self.browser.find_element_by_css_selector('.pb-completion-value')

    @property
    def completion_checkboxes(self):
        return self.browser.find_elements_by_css_selector('.pb-completion-value')

    def expect_checkmarks_visible(self, first_visible, second_visible):
        first_checkmark, second_checkmark = self.checkmarks
        time.sleep(3)
        self.assertEqual(first_checkmark.is_displayed(), first_visible)
        self.assertEqual(second_checkmark.is_displayed(), second_visible)

    def expect_checkbox_checked(self, checked):
        self.assertEqual(bool(self.completion_checkbox.get_attribute('checked')), checked)

    def expect_checkboxes_checked(self, first_checked, second_checked):
        first_checkbox, second_checkbox = self.completion_checkboxes
        self.assertEqual(bool(first_checkbox.get_attribute('checked')), first_checked)
        self.assertEqual(bool(second_checkbox.get_attribute('checked')), second_checked)


class CompletionBlockTest(CompletionBlockTestMixin, ProblemBuilderBaseTest):
    """
    Tests for CompletionBlock inside a normal Problem Builder block.
    """

    def test_simple_flow(self):
        """
        Test a regular Problem Builder block containing one completion block.
        """
        self.pb_wrapper = self.load_scenario('completion_problem.xml', {'include_mcq': False})
        self.wait_for_init()

        # Checkbox of completion block should not have "checked" attribute set initially,
        # and "Submit" should be enabled since leaving checkbox unchecked produces a valid value:
        self.assertIsNone(self.completion_checkbox.get_attribute('checked'))
        self.expect_checkmark_visible(False)
        self.expect_submit_enabled(True)

        # Confirm completion by checking checkbox, and click "Submit":
        self.completion_checkbox.click()
        self.click_submit(self.pb_wrapper)
        # Now, we expect "Submit" to be disabled and the checkmark to be visible:
        self.expect_checkbox_checked(True)
        self.expect_checkmark_visible(True)
        self.expect_submit_enabled(False)

        # Uncheck checkbox
        self.completion_checkbox.click()
        # It should be possible to click "Submit" again, and the checkmark should be hidden:
        self.expect_checkbox_checked(False)
        self.expect_checkmark_visible(False)
        self.expect_submit_enabled(True)

        # Now reload the page:
        self.pb_wrapper = self.reload_page()
        self.wait_for_init()
        # The checkbox should be checked (since that's the value we submitted earlier),
        # and "Submit" should be disabled (to discourage submitting the same answer):
        self.expect_checkbox_checked(True)
        self.expect_checkmark_visible(True)
        self.expect_submit_enabled(False)

    def test_simple_flow_with_peer(self):
        """
        Test a regular Problem Builder block containing one completion block and an MCQ.
        """
        self.pb_wrapper = self.load_scenario("completion_problem.xml", {"include_mcq": True})
        self.wait_for_init()

        # Checkbox of completion block should not have "checked" attribute set initially,
        # and "Submit" should be disabled until an MCQ choice is selected
        self.assertIsNone(self.completion_checkbox.get_attribute('checked'))
        self.expect_checkmark_visible(False)
        self.expect_submit_enabled(False)

        # Confirm completion by checking checkbox:
        self.completion_checkbox.click()
        # Checkmark should be hidden, and "Submit" should be disabled (did not select an MCQ choice yet):
        self.expect_checkbox_checked(True)
        self.expect_checkmark_visible(False)
        self.expect_submit_enabled(False)

        # Select an MCQ choice:
        GetChoices(self.pb_wrapper).select('Yes')
        # "Submit" button should now be enabled:
        self.expect_checkmark_visible(False)
        self.expect_submit_enabled(True)

        # Submit answers
        self.click_submit(self.pb_wrapper)
        # Now, we expect submit to be disabled and the checkmark to be visible:
        self.expect_checkmark_visible(True)
        self.expect_submit_enabled(False)

        # Uncheck checkbox
        self.completion_checkbox.click()
        # It should be possible to click "Submit" again, and the checkmark should be hidden:
        self.expect_checkbox_checked(False)
        self.expect_checkmark_visible(False)
        self.expect_submit_enabled(True)

    def test_multiple_completion_blocks(self):
        """
        Test a regular Problem Builder block containing multiple completion blocks.
        """
        self.pb_wrapper = self.load_scenario("completion_multiple_problem.xml")
        self.wait_for_init()

        first_checkbox, second_checkbox = self.completion_checkboxes

        # Checkboxes of completion blocks should not have "checked" attribute set initially,
        # and "Submit" should be enabled since leaving checkboxes unchecked produces a valid value:
        self.assertIsNone(first_checkbox.get_attribute('checked'))
        self.assertIsNone(second_checkbox.get_attribute('checked'))
        self.expect_checkmarks_visible(False, False)
        self.expect_submit_enabled(True)

        # Confirm completion by checking first checkbox:
        first_checkbox.click()

        self.expect_checkboxes_checked(True, False)
        self.expect_checkmarks_visible(False, False)
        self.expect_submit_enabled(True)

        # Submit answers
        self.click_submit(self.pb_wrapper)
        # Now, we expect "Submit" to be disabled and the checkmarks to be visible:
        self.expect_checkboxes_checked(True, False)
        self.expect_checkmarks_visible(True, True)
        self.expect_submit_enabled(False)

        # Uncheck first checkbox
        first_checkbox.click()
        # It should be possible to click "Submit" again, and the checkmarks should be hidden:
        self.expect_checkboxes_checked(False, False)
        self.expect_checkmarks_visible(False, False)
        self.expect_submit_enabled(True)

        # Now reload the page:
        self.pb_wrapper = self.reload_page()
        self.wait_for_init()

        # The first checkbox should be checked, and the second checkbox should be unchecked
        # (since these are the values we submitted earlier);
        # "Submit" should be disabled (to discourage submitting the same answer):
        self.expect_checkboxes_checked(True, False)
        self.expect_checkmarks_visible(True, True)
        self.expect_submit_enabled(False)


class CompletionStepBlockTest(CompletionBlockTestMixin, MentoringAssessmentBaseTest):
    """
    Tests for CompletionBlock inside a Step Builder block.
    """

    def test_step_with_completion_block(self):
        """
        Test a regular Step Builder block containing one completion block and an MCQ.
        """
        step_builder, controls = self.load_assessment_scenario("completion_step.xml")
        self.wait_for_init()
        self.assertIsNone(self.completion_checkbox.get_attribute('checked'))

        # Submit step 1 (the completion block step), and advance to next step:
        question = self.expect_question_visible(1, step_builder, question_text="Attendance Check")
        self.assertIn("Did you attend the meeting?", question.text)  # Question
        self.assertIn("Yes, I did.", question.text)  # Answer
        self.assertTrue(controls.submit.is_enabled())
        self.assert_hidden(controls.try_again)

        self.completion_checkbox.click()
        self.expect_checkbox_checked(True)
        controls.submit.click()
        self.do_submit_wait(controls, last=False)
        self.wait_until_clickable(controls.next_question)
        controls.next_question.click()

        # Submit step 2 (the MCQ step), and advance to review step:
        question = self.expect_question_visible(2, step_builder)
        GetChoices(question).select("Yes")
        controls.submit.click()
        self.do_submit_wait(controls, last=True)
        self.wait_until_clickable(controls.review)
        controls.review.click()

        self.wait_until_visible(controls.try_again)
        # You can't get a completion block question wrong, but it does count as one correct point by default:
        self.assertIn("You answered 2 questions correctly", step_builder.text)
