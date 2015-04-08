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
from .base_test import MentoringAssessmentBaseTest, GetChoices

CORRECT, INCORRECT, PARTIAL = "correct", "incorrect", "partially-correct"


class MentoringAssessmentTest(MentoringAssessmentBaseTest):
    def _selenium_bug_workaround_scroll_to(self, mentoring, question):
        """Workaround for selenium bug:

        Some version of Selenium has a bug that prevents scrolling
        to radiobuttons before being clicked. The click not taking
        place, when it's outside the view.

        Since the bug does not affect other content, asking Selenium
        to click on the legend first, will properly scroll it.

        It also have it's fair share of issues with the workbench header.

        For this reason we click on the bottom-most element, scrolling to it.
        Then, click on the title of the question (also scrolling to it)
        hopefully, this gives us enough room for the full step with the
        control buttons to fit.
        """
        controls = mentoring.find_element_by_css_selector("div.submit")
        title = question.find_element_by_css_selector("h3.question-title")
        controls.click()
        title.click()

    def assert_hidden(self, elem):
        self.assertFalse(elem.is_displayed())

    def assert_disabled(self, elem):
        self.assertTrue(elem.is_displayed())
        self.assertFalse(elem.is_enabled())

    def assert_clickable(self, elem):
        self.assertTrue(elem.is_displayed())
        self.assertTrue(elem.is_enabled())

    def assert_persistent_elements_present(self, mentoring):
        self.assertIn("A Simple Assessment", mentoring.text)
        self.assertIn("This paragraph is shared between all questions.", mentoring.text)

    def _assert_checkmark(self, mentoring, result):
        """Assert that only the desired checkmark is present."""
        states = {CORRECT: 0, INCORRECT: 0, PARTIAL: 0}
        states[result] += 1

        for name, count in states.items():
            self.assertEqual(len(mentoring.find_elements_by_css_selector(".checkmark-{}".format(name))), count)

    def go_to_workbench_main_page(self):
        self.browser.get(self.live_server_url)

    def freeform_answer(self, number, mentoring, controls, text_input, result, saved_value="", last=False):
        question = self.expect_question_visible(number, mentoring)
        self.assert_persistent_elements_present(mentoring)
        self._selenium_bug_workaround_scroll_to(mentoring, question)

        answer = mentoring.find_element_by_css_selector("textarea.answer.editable")

        self.assertIn("Please answer the questions below.", mentoring.text)
        self.assertIn(self.question_text(number), mentoring.text)
        self.assertIn("What is your goal?", mentoring.text)

        self.assertEquals(saved_value, answer.get_attribute("value"))
        if not saved_value:
            self.assert_disabled(controls.submit)
        self.assert_disabled(controls.next_question)

        answer.clear()
        answer.send_keys(text_input)
        self.assertEquals(text_input, answer.get_attribute("value"))

        self.assert_clickable(controls.submit)
        self.ending_controls(controls, last)
        self.assert_hidden(controls.review)
        self.assert_hidden(controls.try_again)

        controls.submit.click()

        self.do_submit_wait(controls, last)
        self._assert_checkmark(mentoring, result)
        self.do_post(controls, last)

    def ending_controls(self, controls, last):
        if last:
            self.assert_hidden(controls.next_question)
            self.assert_disabled(controls.review)
        else:
            self.assert_disabled(controls.next_question)
            self.assert_hidden(controls.review)

    def selected_controls(self, controls, last):
        self.assert_clickable(controls.submit)
        if last:
            self.assert_hidden(controls.next_question)
            self.assert_disabled(controls.review)
        else:
            self.assert_disabled(controls.next_question)
            self.assert_hidden(controls.review)

    def do_submit_wait(self, controls, last):
        if last:
            self.wait_until_clickable(controls.review)
        else:
            self.wait_until_clickable(controls.next_question)

    def do_post(self, controls, last):
        if last:
            controls.review.click()
        else:
            controls.next_question.click()

    def single_choice_question(self, number, mentoring, controls, choice_name, result, last=False):
        question = self.expect_question_visible(number, mentoring)

        self.assert_persistent_elements_present(mentoring)

        self.assertIn("Do you like this MCQ?", question.text)

        self.assert_disabled(controls.submit)
        self.ending_controls(controls, last)
        self.assert_hidden(controls.try_again)

        choices = GetChoices(question)
        expected_state = {"Yes": False, "Maybe not": False, "I don't understand": False}
        self.assertEquals(choices.state, expected_state)

        choices.select(choice_name)
        expected_state[choice_name] = True
        self.assertEquals(choices.state, expected_state)

        self.selected_controls(controls, last)

        controls.submit.click()

        self.do_submit_wait(controls, last)
        self._assert_checkmark(mentoring, result)

        self.do_post(controls, last)

    def rating_question(self, number, mentoring, controls, choice_name, result, last=False):
        question = self.expect_question_visible(number, mentoring)
        self.assert_persistent_elements_present(mentoring)
        self._selenium_bug_workaround_scroll_to(mentoring, question)
        self.assertIn("How much do you rate this MCQ?", mentoring.text)

        self.assert_disabled(controls.submit)
        self.ending_controls(controls, last)
        self.assert_hidden(controls.review)
        self.assert_hidden(controls.try_again)

        choices = GetChoices(mentoring, ".rating")
        expected_choices = {
            "1 - Not good at all": False,
            "2": False, "3": False, "4": False,
            "5 - Extremely good": False,
            "I don't want to rate it": False,
        }
        self.assertEquals(choices.state, expected_choices)
        choices.select(choice_name)
        expected_choices[choice_name] = True
        self.assertEquals(choices.state, expected_choices)

        self.ending_controls(controls, last)

        controls.submit.click()

        self.do_submit_wait(controls, last)
        self._assert_checkmark(mentoring, result)
        self.do_post(controls, last)

    def peek_at_multiple_choice_question(self, number, mentoring, controls, last=False):
        question = self.expect_question_visible(number, mentoring)
        self.assert_persistent_elements_present(mentoring)
        self._selenium_bug_workaround_scroll_to(mentoring, question)
        self.assertIn("What do you like in this MRQ?", mentoring.text)

        self.assert_disabled(controls.submit)
        self.ending_controls(controls, last)

        return question

    def multiple_choice_question(self, number, mentoring, controls, choice_names, result, last=False):
        question = self.peek_at_multiple_choice_question(number, mentoring, controls, last=last)

        choices = GetChoices(question)
        expected_choices = {
            "Its elegance": False,
            "Its beauty": False,
            "Its gracefulness": False,
            "Its bugs": False,
        }
        self.assertEquals(choices.state, expected_choices)

        for name in choice_names:
            choices.select(name)
            expected_choices[name] = True

        self.assertEquals(choices.state, expected_choices)

        self.selected_controls(controls, last)

        controls.submit.click()

        self.do_submit_wait(controls, last)
        self._assert_checkmark(mentoring, result)
        controls.review.click()

    def peek_at_review(self, mentoring, controls, expected):
        self.wait_until_text_in("You scored {percentage}% on this assessment.".format(**expected), mentoring)
        self.assert_persistent_elements_present(mentoring)
        if expected["num_attempts"] < expected["max_attempts"]:
            self.assertIn("Note: if you retake this assessment, only your final score counts.", mentoring.text)
        if expected["correct"] == 1:
            self.assertIn("You answered 1 questions correctly.".format(**expected), mentoring.text)
        else:
            self.assertIn("You answered {correct} questions correctly.".format(**expected), mentoring.text)
        if expected["partial"] == 1:
            self.assertIn("You answered 1 question partially correctly.", mentoring.text)
        else:
            self.assertIn("You answered {partial} questions partially correctly.".format(**expected), mentoring.text)
        if expected["incorrect"] == 1:
            self.assertIn("You answered 1 question incorrectly.", mentoring.text)
        else:
            self.assertIn("You answered {incorrect} questions incorrectly.".format(**expected), mentoring.text)
        if expected["max_attempts"] == 1:
            self.assertIn("You have used {num_attempts} of 1 submission.".format(**expected), mentoring.text)
        else:
            self.assertIn(
                "You have used {num_attempts} of {max_attempts} submissions.".format(**expected),
                mentoring.text
            )

        self.assert_hidden(controls.submit)
        self.assert_hidden(controls.next_question)
        self.assert_hidden(controls.review)

    def assert_messages_text(self, mentoring, text):
        messages = mentoring.find_element_by_css_selector('.assessment-messages')
        self.assertEqual(messages.text, text)
        self.assertTrue(messages.is_displayed())

    def assert_messages_empty(self, mentoring):
        messages = mentoring.find_element_by_css_selector('.assessment-messages')
        self.assertEqual(messages.text, '')
        self.assertFalse(messages.find_elements_by_xpath('./*'))
        self.assertFalse(messages.is_displayed())

    def test_assessment(self):
        mentoring, controls = self.go_to_assessment("Assessment 1")

        self.freeform_answer(1, mentoring, controls, 'This is the answer', CORRECT)
        self.single_choice_question(2, mentoring, controls, 'Maybe not', INCORRECT)
        self.rating_question(3, mentoring, controls, "5 - Extremely good", CORRECT)
        self.peek_at_multiple_choice_question(4, mentoring, controls, last=True)

        # see if assessment remembers the current step
        self.go_to_workbench_main_page()
        mentoring, controls = self.go_to_assessment("Assessment 1")

        self.multiple_choice_question(4, mentoring, controls, ("Its beauty",), PARTIAL, last=True)

        expected_results = {
            "correct": 2, "partial": 1, "incorrect": 1, "percentage": 63,
            "num_attempts": 1, "max_attempts": 2
        }
        self.peek_at_review(mentoring, controls, expected_results)

        self.assert_messages_text(mentoring, "Assessment additional feedback message text")
        self.assert_clickable(controls.try_again)
        controls.try_again.click()

        self.freeform_answer(
            1, mentoring, controls, 'This is a different answer', CORRECT, saved_value='This is the answer'
        )
        self.single_choice_question(2, mentoring, controls, 'Yes', CORRECT)
        self.rating_question(3, mentoring, controls, "1 - Not good at all", INCORRECT)

        user_selection = ("Its elegance", "Its beauty", "Its gracefulness")
        self.multiple_choice_question(4, mentoring, controls, user_selection, CORRECT, last=True)

        expected_results = {
            "correct": 3, "partial": 0, "incorrect": 1, "percentage": 75,
            "num_attempts": 2, "max_attempts": 2
        }
        self.peek_at_review(mentoring, controls, expected_results)
        self.assert_disabled(controls.try_again)
        self.assert_messages_empty(mentoring)

    def test_single_question_assessment(self):
        """
        No 'Next Question' button on single question assessment.
        """
        mentoring, controls = self.go_to_assessment("Assessment 2")
        self.single_choice_question(0, mentoring, controls, 'Maybe not', INCORRECT, last=True)

        expected_results = {
            "correct": 0, "partial": 0, "incorrect": 1, "percentage": 0,
            "num_attempts": 1, "max_attempts": 2
        }

        self.peek_at_review(mentoring, controls, expected_results)
        self.assert_messages_empty(mentoring)

        controls.try_again.click()
        # this is a wait and assertion all together - it waits until expected text is in mentoring block
        # and it fails with PrmoiseFailed exception if it's not
        self.wait_until_text_in(self.question_text(0), mentoring)
