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
from unittest import mock

import ddt
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait

from .base_test import MentoringBaseTest, ProblemBuilderBaseTest


class MentoringTest(MentoringBaseTest):
    def test_display_submit_false_does_not_display_submit(self):
        mentoring = self.go_to_page('No Display Submit')
        with self.assertRaises(NoSuchElementException):
            mentoring.find_element_by_css_selector('.submit input.input-main')


def _get_mentoring_theme_settings(theme):
    return {
        'package': 'problem_builder',
        'locations': [f'public/themes/{theme}.css']
    }


@ddt.ddt
class ProblemBuilderQuestionnaireBlockTest(ProblemBuilderBaseTest):
    def _get_xblock(self, mentoring, name):
        return mentoring.find_element_by_css_selector(f".xblock-v1[data-name='{name}']")

    def _get_choice(self, questionnaire, choice_index):
        return questionnaire.find_elements_by_css_selector(".choices-list .choice")[choice_index]

    def _get_answer_checkmark(self, answer):
        return answer.find_element_by_xpath("ancestor::node()[3]").find_element_by_css_selector(".answer-checkmark")

    def _get_completion_checkmark(self, completion):
        return completion.find_element_by_xpath("ancestor::node()[4]").find_element_by_css_selector(".submit-result")

    def _get_messages_element(self, mentoring):
        return mentoring.find_element_by_css_selector('.messages')

    def _get_submit(self, mentoring):
        return mentoring.find_element_by_css_selector('.submit input.input-main')

    def _get_controls(self, mentoring):
        answer = self._get_xblock(mentoring, "feedback_answer_1").find_element_by_css_selector('.answer')
        mcq = self._get_xblock(mentoring, "feedback_mcq_2")
        mrq = self._get_xblock(mentoring, "feedback_mrq_3")
        rating = self._get_xblock(mentoring, "feedback_rating_4")
        completion = self._get_xblock(mentoring, "completion_1").find_element_by_css_selector('.pb-completion-value')

        return answer, mcq, mrq, rating, completion

    def _assert_answer(self, answer, results_shown=True):
        self.assertEqual(answer.get_attribute('value'), 'This is the answer')
        answer_checkmark = self._get_answer_checkmark(answer)
        self._assert_checkmark(answer_checkmark, shown=results_shown)

    def _assert_completion(self, completion, results_shown=True):
        self.assertTrue(completion.is_selected())
        completion_checkmark = self._get_completion_checkmark(completion)
        if results_shown:
            self.assertTrue(completion_checkmark.is_displayed())
        else:
            self.assertFalse(completion_checkmark.is_displayed())

    def _assert_checkmark(self, checkmark, correct=True, shown=True):
        result_classes = checkmark.get_attribute('class').split()
        result_label = checkmark.get_attribute('aria-label').strip()
        if shown:
            if correct:
                checkmark_class = 'checkmark-correct'
                checkmark_label = 'Correct'
            else:
                checkmark_class = 'checkmark-incorrect'
                checkmark_label = 'Incorrect'

            self.assertTrue(checkmark.is_displayed())
            self.assertIn(checkmark_class, result_classes)
            self.assertEqual(checkmark_label, result_label)
        else:
            self.assertFalse(checkmark.is_displayed())
            self.assertEqual('', result_label)

    def _assert_mcq(self, mcq, previous_answer_shown=True):
        if previous_answer_shown:
            self._assert_feedback_shown(mcq, 0, "Great!", click_choice_result=True)
        else:
            for i in range(3):
                self._assert_feedback_hidden(mcq, i)
                self._assert_not_checked(mcq, i)

    def _assert_rating(self, rating, previous_answer_shown=True):
        if previous_answer_shown:
            self._assert_feedback_shown(rating, 3, "I love good grades.", click_choice_result=True)
        else:
            for i in range(5):
                self._assert_feedback_hidden(rating, i)
                self._assert_not_checked(rating, i)

    def _assert_feedback_shown(
            self, questionnaire, choice_index, expected_text, click_choice_result=False, success=True
    ):
        """
        Asserts that feedback for given element contains particular text
        If `click_choice_result` is True - clicks on `choice-result` icon before checking feedback visibility:
        MRQ feedbacks are not shown right away
        """
        choice = self._get_choice(questionnaire, choice_index)
        choice_result = choice.find_element_by_css_selector('.choice-result')
        if click_choice_result:
            self.wait_until_clickable(choice_result)
            choice_result.click()

        feedback_popup = choice.find_element_by_css_selector(".choice-tips")
        self._assert_checkmark(choice_result, correct=success)
        self.assertTrue(feedback_popup.is_displayed())
        self.assertEqual(feedback_popup.text, expected_text)

    def _assert_feedback_hidden(self, questionnaire, choice_index):
        choice = self._get_choice(questionnaire, choice_index)
        choice_result = choice.find_element_by_css_selector('.choice-result')
        choice_input = choice.find_element_by_css_selector('input')
        feedback_popup = choice.find_element_by_css_selector(".choice-tips")
        result_classes = choice_result.get_attribute('class').split()

        if choice_input.is_selected():
            self.assertTrue(choice_result.is_displayed())
        self.assertFalse(feedback_popup.is_displayed())
        self.assertNotIn('checkmark-correct', result_classes)
        self.assertNotIn('checkmark-incorrect', result_classes)

    def _assert_not_checked(self, questionnaire, choice_index):
        choice = self._get_choice(questionnaire, choice_index)
        choice_input = choice.find_element_by_css_selector('input')
        self.assertFalse(choice_input.is_selected())

    def _assert_mrq(self, mrq, previous_answer_shown=True):
        if previous_answer_shown:
            self._assert_feedback_shown(
                mrq, 0, "This is something everyone has to like about this MRQ",
                click_choice_result=True
            )
            self._assert_feedback_shown(
                mrq, 1, "This is something everyone has to like about beauty",
                click_choice_result=True, success=False
            )
            self._assert_feedback_shown(mrq, 2, "This MRQ is indeed very graceful", click_choice_result=True)
            self._assert_feedback_shown(mrq, 3, "Nah, there aren't any!", click_choice_result=True, success=False)
        else:
            for i in range(3):
                self._assert_feedback_hidden(mrq, i)
                self._assert_not_checked(mrq, i)

    def _assert_messages(self, messages, shown=True):
        if shown:
            self.assertTrue(messages.is_displayed())
            self.assertEqual(messages.text, "FEEDBACK\nNot done yet")
        else:
            self.assertFalse(messages.is_displayed())
            self.assertEqual(messages.text, "")

    def _standard_filling(self, answer, mcq, mrq, rating, completion):
        # Long answer
        answer.send_keys('This is the answer')
        # MCQ
        self.click_choice(mcq, "Yes")
        # MRQ: Select 1st, 3rd and 4th options
        # First three options are required, so we're making two mistakes:
        # - 2nd option should have been selected
        # - 4th option should *not* have been selected
        self.click_choice(mrq, "Its elegance")
        self.click_choice(mrq, "Its gracefulness")
        self.click_choice(mrq, "Its bugs")
        # Rating
        self.click_choice(rating, "4")
        # Completion - tick the checkbox
        completion.click()

    # mcq and rating can't be reset easily, but it's not required; listing them here to keep method signature similar
    def _clear_filling(self, answer, mcq, mrq, rating, completion):      # pylint: disable=unused-argument
        answer.clear()
        completion.click()
        for checkbox in mrq.find_elements_by_css_selector('.choice input'):
            if checkbox.is_selected():
                checkbox.click()

    def _standard_checks(self, answer, mcq, mrq, rating, completion, messages):
        self.wait_until_visible(messages)

        # Long answer: Previous answer and results visible
        self._assert_answer(answer)
        # MCQ: Previous answer and results visible
        self._assert_mcq(mcq)
        # MRQ: Previous answer and feedback visible
        self._assert_mrq(mrq)
        # Rating: Previous answer and results visible
        self._assert_rating(rating)
        # Completion: Previous answer and results visible
        self._assert_completion(completion)
        # Messages visible
        self._assert_messages(messages)

    def _mcq_hide_previous_answer_checks(self, answer, mcq, mrq, rating, completion, messages):
        self.wait_until_visible(messages)

        # Long answer: Previous answer and results visible
        self._assert_answer(answer)
        # MCQ: Previous answer and results hidden
        self._assert_mcq(mcq, previous_answer_shown=False)
        # MRQ: Previous answer and results hidden
        self._assert_mrq(mrq, previous_answer_shown=False)
        # Rating: Previous answer and results hidden
        self._assert_rating(rating, previous_answer_shown=False)
        # Completion: Previous answer and results visible
        self._assert_completion(completion)
        # Messages visible
        self._assert_messages(messages)

    def _hide_feedback_checks(self, answer, mcq, mrq, rating, completion, messages):
        # Long answer: Previous answer visible and results hidden
        self._assert_answer(answer, results_shown=False)
        # MCQ: Previous answer and results visible
        self._assert_mcq(mcq)
        # MRQ: Previous answer and results visible
        self._assert_mrq(mrq)
        # Rating: Previous answer and results visible
        self._assert_rating(rating)
        # Completion: Previous answer visible and results hidden
        self._assert_completion(completion, results_shown=False)
        # Messages hidden
        self._assert_messages(messages, shown=False)

    def _mcq_hide_previous_answer_hide_feedback_checks(self, answer, mcq, mrq, rating, completion, messages):
        # Long answer: Previous answer visible and results hidden
        self._assert_answer(answer, results_shown=False)
        # MCQ: Previous answer and results hidden
        self._assert_mcq(mcq, previous_answer_shown=False)
        # MRQ: Previous answer and results hidden
        self._assert_mrq(mrq, previous_answer_shown=False)
        # Rating: Previous answer and feedback hidden
        self._assert_rating(rating, previous_answer_shown=False)
        # Completion: Previous answer visible and results hidden
        self._assert_completion(completion, results_shown=False)
        # Messages hidden
        self._assert_messages(messages, shown=False)

    def reload_student_view(self):
        # Load another page (the home page), then go back to the page we want. This is the only reliable way to reload.
        self.browser.get(self.live_server_url + '/')
        wait = WebDriverWait(self.browser, self.timeout)

        def did_load_homepage(driver):
            title = driver.find_element_by_css_selector('h1.title')
            return title and title.text == "XBlock scenarios"

        wait.until(did_load_homepage, "Workbench home page should have loaded")
        mentoring = self.go_to_view("student_view")
        submit = self._get_submit(mentoring)
        self.wait_until_visible(submit)
        return mentoring

    def test_feedback_and_messages_not_shown_on_first_load(self):
        mentoring = self.load_scenario("feedback_persistence.xml")
        answer, mcq, mrq, rating, completion = self._get_controls(mentoring)
        messages = self._get_messages_element(mentoring)
        submit = self._get_submit(mentoring)

        answer_checkmark = self._get_answer_checkmark(answer)
        self._assert_checkmark(answer_checkmark, shown=False)
        for i in range(3):
            self._assert_feedback_hidden(mcq, i)
        for i in range(4):
            self._assert_feedback_hidden(mrq, i)
        for i in range(5):
            self._assert_feedback_hidden(rating, i)
        completion_checkmark = self._get_completion_checkmark(completion)
        self.assertFalse(completion_checkmark.is_displayed())
        self.assertFalse(messages.is_displayed())
        self.assertFalse(submit.is_enabled())

    def test_persists_feedback_on_page_reload(self):
        options = {
            'pb_mcq_hide_previous_answer': False,
            'pb_hide_feedback_if_attempts_remain': False
        }
        self._test_persistence(options, "_standard_checks")

    def test_does_not_persist_feedback_on_page_reload_if_disabled(self):
        options = {
            'pb_mcq_hide_previous_answer': False,
            'pb_hide_feedback_if_attempts_remain': True
        }
        self._test_persistence(options, "_hide_feedback_checks")

    def test_does_not_persist_mcq_on_page_reload_if_disabled(self):
        options = {
            'pb_mcq_hide_previous_answer': True,
            'pb_hide_feedback_if_attempts_remain': False
        }
        self._test_persistence(options, "_mcq_hide_previous_answer_checks")

    def test_does_not_persist_mcq_and_feedback_on_page_reload_if_disabled(self):
        options = {
            'pb_mcq_hide_previous_answer': True,
            'pb_hide_feedback_if_attempts_remain': True
        }
        self._test_persistence(options, "_mcq_hide_previous_answer_hide_feedback_checks")

    def _test_persistence(self, options, after_reload_checks):
        with mock.patch("problem_builder.mentoring.MentoringBlock.get_options") as patched_options:
            patched_options.return_value = options
            mentoring = self.load_scenario("feedback_persistence.xml")
            answer, mcq, mrq, rating, completion = self._get_controls(mentoring)
            messages = self._get_messages_element(mentoring)

            self._standard_filling(answer, mcq, mrq, rating, completion)
            self.click_submit(mentoring)
            self._standard_checks(answer, mcq, mrq, rating, completion, messages)

            # Now reload the page...
            mentoring = self.reload_student_view()
            answer, mcq, mrq, rating, completion = self._get_controls(mentoring)
            messages = self._get_messages_element(mentoring)
            submit = self._get_submit(mentoring)

            # ... and see if previous answers, results, feedback are shown/hidden correctly
            getattr(self, after_reload_checks)(answer, mcq, mrq, rating, completion, messages)

            # After reloading, submit is enabled only when:
            #  - feedback is hidden; and
            #  - previous MCQ/MRQ answers are visible.
            # When feedback is visible there's no need to resubmit the same answer;
            # and when previous MCQ/MRQ answers are hidden, submit is disabled until you select some options.
            if options['pb_hide_feedback_if_attempts_remain'] and not options['pb_mcq_hide_previous_answer']:
                self.assertTrue(submit.is_enabled())
            else:
                self.assertFalse(submit.is_enabled())

            # When student makes changes, submit is enabled again.
            self.click_choice(mcq, "Maybe not")
            self.click_choice(mrq, "Its elegance")
            self.click_choice(rating, "2")
            self.assertTrue(submit.is_enabled())

    def test_given_perfect_score_in_past_loads_current_result(self):
        mentoring = self.load_scenario("feedback_persistence.xml")
        answer, mcq, mrq, rating, completion = self._get_controls(mentoring)
        messages = self._get_messages_element(mentoring)

        answer.send_keys('This is the answer')
        self.click_choice(mcq, "Yes")
        # 1st, 3rd and 4th options, first three are correct, i.e. two mistakes: 2nd and 4th
        self.click_choice(mrq, "Its elegance")
        self.click_choice(mrq, "Its gracefulness")
        self.click_choice(mrq, "Its beauty")
        self.click_choice(rating, "4")
        completion.click()
        self.click_submit(mentoring)

        # precondition - verifying 100% score achieved
        self.assertEqual(answer.get_attribute('value'), 'This is the answer')
        self._assert_feedback_shown(mcq, 0, "Great!", click_choice_result=True)
        self._assert_feedback_shown(
            mrq, 0, "This is something everyone has to like about this MRQ",
            click_choice_result=True
        )
        self._assert_feedback_shown(
            mrq, 1, "This is something everyone has to like about beauty",
            click_choice_result=True
        )
        self._assert_feedback_shown(mrq, 2, "This MRQ is indeed very graceful", click_choice_result=True)
        self._assert_feedback_shown(mrq, 3, "Nah, there aren't any!", click_choice_result=True)
        self._assert_feedback_shown(rating, 3, "I love good grades.", click_choice_result=True)
        self.assertTrue(completion.is_selected())
        self.assertTrue(messages.is_displayed())
        self.assertEqual(messages.text, "FEEDBACK\nAll Good")

        self._clear_filling(answer, mcq, mrq, rating, completion)
        self._standard_filling(answer, mcq, mrq, rating, completion)
        self.click_submit(mentoring)
        self._standard_checks(answer, mcq, mrq, rating, completion, messages)

        # now, reload the page and make sure LATEST submission is loaded and feedback is shown
        mentoring = self.reload_student_view()
        answer, mcq, mrq, rating, completion = self._get_controls(mentoring)
        messages = self._get_messages_element(mentoring)
        self._standard_checks(answer, mcq, mrq, rating, completion, messages)

    def test_partial_mrq_is_not_completed(self):
        mentoring = self.load_scenario("feedback_persistence.xml")
        answer, mcq, mrq, rating, completion = self._get_controls(mentoring)
        messages = self._get_messages_element(mentoring)

        answer.send_keys('This is the answer')
        self.click_choice(mcq, "Yes")
        # 1st, 3rd and 4th options, first three are correct, i.e. two mistakes: 2nd and 4th
        self.click_choice(mrq, "Its elegance")
        self.click_choice(mrq, "Its gracefulness")
        self.click_choice(rating, "4")
        completion.click()
        self.click_submit(mentoring)

        def assert_state(answer, mcq, mrq, rating, completion, messages):
            self.wait_until_visible(messages)
            self.assertEqual(answer.get_attribute('value'), 'This is the answer')
            self._assert_feedback_shown(mcq, 0, "Great!", click_choice_result=True)
            self._assert_feedback_shown(
                mrq, 0, "This is something everyone has to like about this MRQ",
                click_choice_result=True
            )
            self._assert_feedback_shown(
                mrq, 1, "This is something everyone has to like about beauty",
                click_choice_result=True, success=False
            )
            self._assert_feedback_shown(mrq, 2, "This MRQ is indeed very graceful", click_choice_result=True)
            self._assert_feedback_shown(mrq, 3, "Nah, there aren't any!", click_choice_result=True)
            self._assert_feedback_shown(rating, 3, "I love good grades.", click_choice_result=True)
            self.assertTrue(completion.is_selected())
            self.assertTrue(messages.is_displayed())
            self.assertEqual(messages.text, "FEEDBACK\nNot done yet")

        assert_state(answer, mcq, mrq, rating, completion, messages)

        # now, reload the page and make sure the same result is shown
        mentoring = self.reload_student_view()
        answer, mcq, mrq, rating, completion = self._get_controls(mentoring)
        messages = self._get_messages_element(mentoring)
        assert_state(answer, mcq, mrq, rating, completion, messages)

    @ddt.unpack
    @ddt.data(
        # Questionnaire with tips.
        ("feedback_persistence_mcq_tips.xml", 'MCQ', True, False),
        ("feedback_persistence_mrq_tips.xml", 'MRQ', True, False),
        # Like the above but instead of tips in MCQ/MRQ
        # has a question level feedback. This feedback should also be suppressed.
        ("feedback_persistence_mcq_general_feedback.xml", 'MCQ', False, True),
        ("feedback_persistence_mrq_general_feedback.xml", 'MRQ', False, True),
        # These examples have both the choice tips and the general feedback.
        ("feedback_persistence_mcq_general_feedback_and_tips.xml", 'MCQ', True, True),
        ("feedback_persistence_mrq_general_feedback_and_tips.xml", 'MRQ', True, True),
        # And these have neither the tips nor the general feedback.
        ("feedback_persistence_mcq_no_feedback.xml", 'MCQ', False, False),
        ("feedback_persistence_mrq_no_feedback.xml", 'MRQ', False, False),
    )
    def test_feedback_persistence_tips(self, scenario, question_type, has_tips, has_feedback):
        tips_selector = '.choice-tips'
        feedback_selector = '.feedback'
        # Tests whether feedback (global message and choice tips) is hidden on reload.
        with mock.patch("problem_builder.mentoring.MentoringBlock.get_options") as patched_options:
            patched_options.return_value = {'pb_mcq_hide_previous_answer': True}
            mentoring = self.load_scenario(scenario)
            questionnaire = self._get_xblock(mentoring, "feedback_questionnaire")
            choice = self._get_choice(questionnaire, 0)
            choice_label = choice.find_element_by_css_selector('label')
            choice_result = choice.find_element_by_css_selector('.choice-result')
            tips = mentoring.find_element_by_css_selector(tips_selector)
            feedback = mentoring.find_element_by_css_selector(feedback_selector)

            self.assertFalse(tips.is_displayed())
            self.assertFalse(feedback.is_displayed())

            # Select choice.
            choice_label.click()
            self.click_submit(mentoring)

            # If the question has no general feedback and no tips,
            # nothing should be displayed.
            if not has_feedback and not has_tips:
                self.assertFalse(feedback.is_displayed())
                self.assertFalse(tips.is_displayed())
            # If there is general feedback, but no choice tips,
            # general feedback is displayed after submitting the answer.
            if has_feedback and not has_tips:
                self.assertTrue(feedback.is_displayed())
                self.assertFalse(tips.is_displayed())
            # If there are tips but no feedback, the result depends on question type:
            # - the tip is displayed by MCQs
            # - nothing is displayed by MRQs
            if has_tips and not has_feedback:
                self.assertFalse(feedback.is_displayed())
                if question_type == 'MCQ':
                    self.assertTrue(tips.is_displayed())
                elif question_type == 'MRQ':
                    self.assertFalse(tips.is_displayed())
            # If there are both tips and general feedback,
            # the result depends on the question type:
            # - the tip is displayed by MCQs
            # - general feedback is displayed by MRQs.
            if has_feedback and has_tips:
                if question_type == 'MCQ':
                    self.assertTrue(tips.is_displayed())
                    self.assertFalse(feedback.is_displayed())
                elif question_type == 'MRQ':
                    self.assertTrue(feedback.is_displayed())
                    self.assertFalse(tips.is_displayed())

            # Click the result icon; this hides the general feedback and displays
            # the choice tip, if present.
            choice_result.click()

            self.assertFalse(feedback.is_displayed())
            if has_tips:
                self.assertTrue(tips.is_displayed())

            # Reload the page.
            mentoring = self.reload_student_view()
            tips = mentoring.find_element_by_css_selector(tips_selector)
            feedback = mentoring.find_element_by_css_selector(feedback_selector)
            # After reloading the page, neither the tips nor the feedback should be displayed.
            self.assertFalse(tips.is_displayed())
            self.assertFalse(feedback.is_displayed())

    @ddt.data(
        (0, "Yes", "Great!"),
        (1, "Maybe not", "Ah, damn."),
        (2, "I don't understand", "Really?")
    )
    @ddt.unpack
    def test_clicking_result_icon_shows_tips(self, choice_index, choice_text, expected_tip):
        mentoring = self.load_scenario("feedback_persistence_mcq_tips.xml")
        mcq = self._get_xblock(mentoring, "feedback_questionnaire")
        question_title = mentoring.find_element_by_css_selector('.question-title')
        choice = self._get_choice(mcq, choice_index)
        choice_result = choice.find_element_by_css_selector('.choice-result')
        choice_tips = choice.find_element_by_css_selector('.choice-tips')

        def assert_tip():
            self.wait_until_visible(choice_tips)
            tip = choice_tips.find_element_by_css_selector('.tip')
            self.assertEqual(tip.text, expected_tip)

        # Answer question
        self.click_choice(mcq, choice_text)
        # Submit answer
        self.click_submit(mentoring)
        # Tip for selected choice should be visible and match expected tip
        assert_tip()
        # Random click to make tip disappear
        question_title.click()
        # Tip for selected choice should be hidden
        self.wait_until_hidden(choice_tips)
        # Click result icon to show tips
        choice_result.click()
        # Tip for selected choice should be visible and match expected tip
        assert_tip()
