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
from ddt import ddt, unpack, data
from .base_test import MentoringAssessmentBaseTest, GetChoices

CORRECT, INCORRECT, PARTIAL = "correct", "incorrect", "partially-correct"


@ddt
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

    def peek_at_multiple_response_question(
            self, number, mentoring, controls, last=False, extended_feedback=False, alternative_review=False
    ):
        question = self.expect_question_visible(number, mentoring)
        self.assert_persistent_elements_present(mentoring)
        self._selenium_bug_workaround_scroll_to(mentoring, question)
        self.assertIn("What do you like in this MRQ?", mentoring.text)

        if extended_feedback:
            self.assert_disabled(controls.submit)
            if alternative_review:
                self.assert_clickable(controls.review_link)
                self.assert_hidden(controls.try_again)
            else:
                self.assert_clickable(controls.review)
        else:
            self.assert_disabled(controls.submit)
            self.ending_controls(controls, last)

        return question

    def multiple_response_question(self, number, mentoring, controls, choice_names, result, last=False):
        question = self.peek_at_multiple_response_question(number, mentoring, controls, last=last)

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

    def peek_at_review(self, mentoring, controls, expected, extended_feedback=False):
        self.wait_until_text_in("You scored {percentage}% on this assessment.".format(**expected), mentoring)
        self.assert_persistent_elements_present(mentoring)
        if expected["max_attempts"] > 0 and expected["num_attempts"] < expected["max_attempts"]:
            self.assertFalse(mentoring.find_elements_by_css_selector('.review-list'))
        elif extended_feedback:
            for q_type in ['correct', 'incorrect', 'partial']:
                self.assertEqual(len(mentoring.find_elements_by_css_selector('.%s-list li' % q_type)), expected[q_type])
        else:
            self.assertFalse(mentoring.find_elements_by_css_selector('.review-list'))
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
        elif expected["max_attempts"] == 0:
            self.assertNotIn("You have used", mentoring.text)
        else:
            self.assertIn(
                "You have used {num_attempts} of {max_attempts} submissions.".format(**expected),
                mentoring.text
            )

        self.assert_hidden(controls.submit)
        self.assert_hidden(controls.next_question)
        self.assert_hidden(controls.review)
        self.assert_hidden(controls.review_link)

    def assert_message_text(self, mentoring, text):
        message_wrapper = mentoring.find_element_by_css_selector('.assessment-message')
        self.assertEqual(message_wrapper.text, text)
        self.assertTrue(message_wrapper.is_displayed())

    def extended_feedback_checks(self, mentoring, controls, expected_results):
        # Multiple choice is third correctly answered question
        self.assert_hidden(controls.review_link)
        mentoring.find_elements_by_css_selector('.correct-list li a')[2].click()
        self.peek_at_multiple_response_question(4, mentoring, controls, extended_feedback=True, alternative_review=True)
        # Four correct items, plus the overall correct indicator.
        correct_marks = mentoring.find_elements_by_css_selector('.checkmark-correct')
        incorrect_marks = mentoring.find_elements_by_css_selector('.checkmark-incorrect')
        self.assertEqual(len(correct_marks), 5)
        self.assertEqual(len(incorrect_marks), 0)
        item_feedbacks = [
            "This is something everyone has to like about this MRQ",
            "This is something everyone has to like about this MRQ",
            "This MRQ is indeed very graceful",
            "Nah, there aren't any!"
        ]
        self.popup_check(mentoring, item_feedbacks, prefix='div[data-name="mrq_1_1"]', do_submit=False)
        self.assert_hidden(controls.review)
        self.assert_disabled(controls.submit)
        controls.review_link.click()
        self.peek_at_review(mentoring, controls, expected_results, extended_feedback=True)
        # Rating question, right before MRQ.
        mentoring.find_elements_by_css_selector('.incorrect-list li a')[0].click()
        # Should be possible to visit the MRQ from there.
        self.wait_until_clickable(controls.next_question)
        controls.next_question.click()
        self.peek_at_multiple_response_question(4, mentoring, controls, extended_feedback=True, alternative_review=True)

    @data(
        {"max_attempts": 0, "extended_feedback": False},  # Note '0' means unlimited attempts
        {"max_attempts": 1, "extended_feedback": False},
        {"max_attempts": 4, "extended_feedback": False},
        {"max_attempts": 2, "extended_feedback": True},
    )
    def test_assessment(self, params):
        mentoring, controls = self.load_assessment_scenario("assessment.xml", params)
        max_attempts = params['max_attempts']
        extended_feedback = params['extended_feedback']

        self.freeform_answer(1, mentoring, controls, 'This is the answer', CORRECT)
        self.single_choice_question(2, mentoring, controls, 'Maybe not', INCORRECT)
        self.rating_question(3, mentoring, controls, "5 - Extremely good", CORRECT)
        self.peek_at_multiple_response_question(4, mentoring, controls, last=True)

        # see if assessment remembers the current step
        self.go_to_workbench_main_page()
        mentoring, controls = self.go_to_assessment()

        self.multiple_response_question(4, mentoring, controls, ("Its beauty",), PARTIAL, last=True)

        expected_results = {
            "correct": 2, "partial": 1, "incorrect": 1, "percentage": 63,
            "num_attempts": 1, "max_attempts": max_attempts
        }
        self.peek_at_review(mentoring, controls, expected_results, extended_feedback=extended_feedback)

        if max_attempts == 1:
            self.assert_message_text(mentoring, "Note: you have used all attempts. Continue to the next unit.")
            self.assert_disabled(controls.try_again)
            return

        # The on-assessment-review message is shown if attempts remain:
        self.assert_message_text(mentoring, "Assessment additional feedback message text")
        self.assert_clickable(controls.try_again)
        controls.try_again.click()

        self.freeform_answer(
            1, mentoring, controls, 'This is a different answer', CORRECT, saved_value='This is the answer'
        )
        self.single_choice_question(2, mentoring, controls, 'Yes', CORRECT)
        self.rating_question(3, mentoring, controls, "1 - Not good at all", INCORRECT)

        user_selection = ("Its elegance", "Its beauty", "Its gracefulness")
        self.multiple_response_question(4, mentoring, controls, user_selection, CORRECT, last=True)

        expected_results = {
            "correct": 3, "partial": 0, "incorrect": 1, "percentage": 75,
            "num_attempts": 2, "max_attempts": max_attempts
        }
        self.peek_at_review(mentoring, controls, expected_results, extended_feedback=extended_feedback)
        if max_attempts == 2:
            self.assert_disabled(controls.try_again)
        else:
            self.assert_clickable(controls.try_again)
        if 1 <= max_attempts <= 2:
            self.assert_message_text(mentoring, "Note: you have used all attempts. Continue to the next unit.")
        else:
            self.assert_message_text(mentoring, "Assessment additional feedback message text")
        if extended_feedback:
            self.extended_feedback_checks(mentoring, controls, expected_results)

    def test_review_tips(self):
        params = {
            "max_attempts": 3,
            "extended_feedback": False,
            "include_review_tips": True
        }
        mentoring, controls = self.load_assessment_scenario("assessment.xml", params)

        # Get one question wrong and one partially wrong on attempt 1 of 3: ####################
        self.freeform_answer(1, mentoring, controls, 'This is the answer', CORRECT)
        self.single_choice_question(2, mentoring, controls, 'Maybe not', INCORRECT)
        self.rating_question(3, mentoring, controls, "5 - Extremely good", CORRECT)
        self.multiple_response_question(4, mentoring, controls, ("Its beauty",), PARTIAL, last=True)

        # The review tips for MCQ 2 and the MRQ should be shown:
        review_tips = mentoring.find_element_by_css_selector('.assessment-review-tips')
        self.assertTrue(review_tips.is_displayed())
        self.assertIn('You might consider reviewing the following items', review_tips.text)
        self.assertIn('Take another look at', review_tips.text)
        self.assertIn('Lesson 1', review_tips.text)
        self.assertNotIn('Lesson 2', review_tips.text)  # This MCQ was correct
        self.assertIn('Lesson 3', review_tips.text)
        # The on-assessment-review message is also shown if attempts remain:
        self.assert_message_text(mentoring, "Assessment additional feedback message text")

        self.assert_clickable(controls.try_again)
        controls.try_again.click()

        # Get no questions wrong on attempt 2 of 3: ############################################
        self.freeform_answer(1, mentoring, controls, 'This is the answer', CORRECT, saved_value='This is the answer')
        self.single_choice_question(2, mentoring, controls, 'Yes', CORRECT)
        self.rating_question(3, mentoring, controls, "5 - Extremely good", CORRECT)
        user_selection = ("Its elegance", "Its beauty", "Its gracefulness")
        self.multiple_response_question(4, mentoring, controls, user_selection, CORRECT, last=True)

        self.assert_message_text(mentoring, "Assessment additional feedback message text")
        self.assertFalse(review_tips.is_displayed())

        self.assert_clickable(controls.try_again)
        controls.try_again.click()

        # Get some questions wrong again on attempt 3 of 3:
        self.freeform_answer(1, mentoring, controls, 'This is the answer', CORRECT, saved_value='This is the answer')
        self.single_choice_question(2, mentoring, controls, 'Maybe not', INCORRECT)
        self.rating_question(3, mentoring, controls, "1 - Not good at all", INCORRECT)
        self.multiple_response_question(4, mentoring, controls, ("Its beauty",), PARTIAL, last=True)

        # The review tips will not be shown because no attempts remain:
        self.assertFalse(review_tips.is_displayed())

    def test_single_question_assessment(self):
        """
        No 'Next Question' button on single question assessment.
        """
        mentoring, controls = self.load_assessment_scenario("assessment_single.xml", {"max_attempts": 2})
        self.single_choice_question(0, mentoring, controls, 'Maybe not', INCORRECT, last=True)

        expected_results = {
            "correct": 0, "partial": 0, "incorrect": 1, "percentage": 0,
            "num_attempts": 1, "max_attempts": 2
        }

        self.peek_at_review(mentoring, controls, expected_results)
        self.assert_message_text(
            mentoring,
            "Note: if you retake this assessment, only your final score counts. "
            "If you would like to keep this score, please continue to the next unit."
        )

        self.wait_until_clickable(controls.try_again)
        controls.try_again.click()
        self.wait_until_hidden(controls.try_again)
        self.assertIn(self.question_text(0), mentoring.text)
