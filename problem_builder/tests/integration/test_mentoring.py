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
from selenium.webdriver.support.ui import WebDriverWait
from .base_test import MentoringBaseTest, MentoringAssessmentBaseTest, GetChoices, ProblemBuilderBaseTest


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

    def assert_status_icon_color(self, color, question_text):
        mentoring, controls = self.load_assessment_scenario('assessment_single.xml', {"max_attempts": 2})
        question = self.expect_question_visible(0, mentoring, question_text=question_text)
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
        ('lms', "#c1373f", "Question"),
        ('apros', "#ff0000", "QUESTION")
    )
    def test_lms_theme_applied(self, theme, expected_color, question_text):
        with mock.patch("problem_builder.mentoring.MentoringBlock.get_theme") as patched_theme:
            patched_theme.return_value = _get_mentoring_theme_settings(theme)
            self.assert_status_icon_color(expected_color, question_text)


@ddt.ddt
class ProblemBuilderQuestionnaireBlockTest(ProblemBuilderBaseTest):
    def _get_xblock(self, mentoring, name):
        return mentoring.find_element_by_css_selector(".xblock-v1[data-name='{}']".format(name))

    def _get_choice(self, questionnaire, choice_index):
        return questionnaire.find_elements_by_css_selector(".choices-list .choice")[choice_index]

    def _get_messages_element(self, mentoring):
        return mentoring.find_element_by_css_selector('.messages')

    def _get_controls(self, mentoring):
        answer = self._get_xblock(mentoring, "feedback_answer_1").find_element_by_css_selector('.answer')
        mcq = self._get_xblock(mentoring, "feedback_mcq_2")
        mrq = self._get_xblock(mentoring, "feedback_mrq_3")
        rating = self._get_xblock(mentoring, "feedback_rating_4")

        return answer, mcq, mrq, rating

    def _assert_checkmark(self, checkmark, shown=True, checkmark_class=None):
        choice_result_classes = checkmark.get_attribute('class').split()
        if shown:
            self.assertTrue(checkmark.is_displayed())
            self.assertIn(checkmark_class, choice_result_classes)
        else:
            self.assertFalse(checkmark.is_displayed())

    def _assert_feedback_showed(self, questionnaire, choice_index, expected_text,
                                click_choice_result=False, success=True):
        """
        Asserts that feedback for given element contains particular text
        If `click_choice_result` is True - clicks on `choice-result` icon before checking feedback visibility:
        MRQ feedbacks are not shown right away
        """
        choice = self._get_choice(questionnaire, choice_index)
        choice_result = choice.find_element_by_css_selector('.choice-result')
        if click_choice_result:
            choice_result.click()

        feedback_popup = choice.find_element_by_css_selector(".choice-tips")
        checkmark_class = 'checkmark-correct' if success else 'checkmark-incorrect'
        self._assert_checkmark(choice_result, shown=True, checkmark_class=checkmark_class)
        self.assertTrue(feedback_popup.is_displayed())
        self.assertEqual(feedback_popup.text, expected_text)

    def _assert_feedback_hidden(self, questionnaire, choice_index):
        choice = self._get_choice(questionnaire, choice_index)
        choice_result = choice.find_element_by_css_selector('.choice-result')
        feedback_popup = choice.find_element_by_css_selector(".choice-tips")
        choice_result_classes = choice_result.get_attribute('class').split()

        self.assertTrue(choice_result.is_displayed())
        self.assertFalse(feedback_popup.is_displayed())
        self.assertNotIn('checkmark-correct', choice_result_classes)
        self.assertNotIn('checkmark-incorrect', choice_result_classes)

    def _assert_not_checked(self, questionnaire, choice_index):
        choice = self._get_choice(questionnaire, choice_index)
        choice_input = choice.find_element_by_css_selector('input')
        self.assertFalse(choice_input.is_selected())

    def _standard_filling(self, answer, mcq, mrq, rating):
        self.scroll_to(answer)
        answer.send_keys('This is the answer')
        self.scroll_to(mcq)
        self.click_choice(mcq, "Yes")
        # 1st, 3rd and 4th options, first three are correct, i.e. two mistakes: 2nd and 4th
        self.scroll_to(mrq, 300)
        self.click_choice(mrq, "Its elegance")
        self.click_choice(mrq, "Its gracefulness")
        self.click_choice(mrq, "Its bugs")
        self.scroll_to(rating)
        self.click_choice(rating, "4")

    # mcq and rating can't be reset easily, but it's not required; listing them here to keep method signature similar
    def _clear_filling(self, answer, mcq, mrq, rating):      # pylint: disable=unused-argument
        answer.clear()
        for checkbox in mrq.find_elements_by_css_selector('.choice input'):
            if checkbox.is_selected():
                checkbox.click()

    def _standard_checks(self, answer, mcq, mrq, rating, messages):
        self.scroll_to(answer)
        self.assertEqual(answer.get_attribute('value'), 'This is the answer')
        self.scroll_to(mcq)
        self._assert_feedback_showed(mcq, 0, "Great!", click_choice_result=True)
        self.scroll_to(mrq, 300)
        self._assert_feedback_showed(
            mrq, 0, "This is something everyone has to like about this MRQ",
            click_choice_result=True
        )
        self._assert_feedback_showed(
            mrq, 1, "This is something everyone has to like about beauty",
            click_choice_result=True, success=False
        )
        self._assert_feedback_showed(mrq, 2, "This MRQ is indeed very graceful", click_choice_result=True)
        self._assert_feedback_showed(mrq, 3, "Nah, there aren't any!", click_choice_result=True, success=False)
        self.scroll_to(rating)
        self._assert_feedback_showed(rating, 3, "I love good grades.", click_choice_result=True)
        self.assertTrue(messages.is_displayed())
        self.scroll_to(messages)
        self.assertEqual(messages.text, "FEEDBACK\nNot done yet")

    def _feedback_customized_checks(self, answer, mcq, mrq, rating, messages):
        # Long answer: Previous answer and feedback visible
        self.scroll_to(answer)
        self.assertEqual(answer.get_attribute('value'), 'This is the answer')
        # MCQ: Previous answer and feedback hidden
        self.scroll_to(mcq)
        for i in range(3):
            self._assert_feedback_hidden(mcq, i)
            self._assert_not_checked(mcq, i)
        # MRQ: Previous answer and feedback visible
        self.scroll_to(mrq, 300)
        self._assert_feedback_showed(
            mrq, 0, "This is something everyone has to like about this MRQ",
            click_choice_result=True
        )
        self._assert_feedback_showed(
            mrq, 1, "This is something everyone has to like about beauty",
            click_choice_result=True, success=False
        )
        self._assert_feedback_showed(mrq, 2, "This MRQ is indeed very graceful", click_choice_result=True)
        self._assert_feedback_showed(mrq, 3, "Nah, there aren't any!", click_choice_result=True, success=False)
        # Rating: Previous answer and feedback hidden
        self.scroll_to(rating)
        for i in range(5):
            self._assert_feedback_hidden(rating, i)
            self._assert_not_checked(rating, i)
        # Messages
        self.assertTrue(messages.is_displayed())
        self.scroll_to(messages)
        self.assertEqual(messages.text, "FEEDBACK\nNot done yet")

    def reload_student_view(self):
        # Load another page (the home page), then go back to the page we want. This is the only reliable way to reload.
        self.browser.get(self.live_server_url + '/')
        wait = WebDriverWait(self.browser, self.timeout)

        def did_load_homepage(driver):
            title = driver.find_element_by_css_selector('h1.title')
            return title and title.text == "XBlock scenarios"
        wait.until(did_load_homepage, u"Workbench home page should have loaded")
        mentoring = self.go_to_view("student_view")
        self.wait_until_visible(self._get_xblock(mentoring, "feedback_mcq_2"))
        return mentoring

    def test_feedbacks_and_messages_is_not_shown_on_first_load(self):
        mentoring = self.load_scenario("feedback_persistence.xml")
        answer, mcq, mrq, rating = self._get_controls(mentoring)
        messages = self._get_messages_element(mentoring)
        submit = mentoring.find_element_by_css_selector('.submit input.input-main')

        answer_checkmark = answer.find_element_by_xpath("parent::*").find_element_by_css_selector(".answer-checkmark")

        self._assert_checkmark(answer_checkmark, shown=False)
        for i in range(3):
            self._assert_feedback_hidden(mcq, i)
        for i in range(4):
            self._assert_feedback_hidden(mrq, i)
        for i in range(5):
            self._assert_feedback_hidden(rating, i)
        self.assertFalse(messages.is_displayed())
        self.assertFalse(submit.is_enabled())

    def test_persists_feedback_on_page_reload(self):
        mentoring = self.load_scenario("feedback_persistence.xml")
        answer, mcq, mrq, rating = self._get_controls(mentoring)
        messages = self._get_messages_element(mentoring)

        self._standard_filling(answer, mcq, mrq, rating)
        self.click_submit(mentoring)
        self._standard_checks(answer, mcq, mrq, rating, messages)

        # now, reload the page and do the same checks again
        mentoring = self.reload_student_view()
        answer, mcq, mrq, rating = self._get_controls(mentoring)
        messages = self._get_messages_element(mentoring)
        submit = mentoring.find_element_by_css_selector('.submit input.input-main')

        self._standard_checks(answer, mcq, mrq, rating, messages)
        # after reloading submit is disabled...
        self.assertFalse(submit.is_enabled())

        # ...until some changes are done
        self.click_choice(mrq, "Its elegance")
        self.assertTrue(submit.is_enabled())

    def test_does_not_persist_mcq_feedback_on_page_reload_if_disabled(self):
        with mock.patch("problem_builder.mentoring.MentoringBlock.get_options") as patched_options:
            patched_options.return_value = {'pb_mcq_hide_previous_answer': True}
            mentoring = self.load_scenario("feedback_persistence.xml")
            answer, mcq, mrq, rating = self._get_controls(mentoring)
            messages = self._get_messages_element(mentoring)

            self._standard_filling(answer, mcq, mrq, rating)
            self.click_submit(mentoring)
            self._standard_checks(answer, mcq, mrq, rating, messages)

            # now, reload the page and see if previous answers and results for MCQs are hidden
            mentoring = self.reload_student_view()
            answer, mcq, mrq, rating = self._get_controls(mentoring)
            messages = self._get_messages_element(mentoring)
            submit = mentoring.find_element_by_css_selector('.submit input.input-main')

            self._feedback_customized_checks(answer, mcq, mrq, rating, messages)
            # after reloading submit is disabled...
            self.assertFalse(submit.is_enabled())

            # ... until student answers MCQs again
            self.scroll_to(mcq)
            self.click_choice(mcq, "Maybe not")
            self.scroll_to(rating)
            self.click_choice(rating, "2")
            self.scroll_to(submit)
            self.assertTrue(submit.is_enabled())

    def test_given_perfect_score_in_past_loads_current_result(self):
        mentoring = self.load_scenario("feedback_persistence.xml")
        answer, mcq, mrq, rating = self._get_controls(mentoring)
        messages = self._get_messages_element(mentoring)

        answer.send_keys('This is the answer')
        self.click_choice(mcq, "Yes")
        # 1st, 3rd and 4th options, first three are correct, i.e. two mistakes: 2nd and 4th
        self.click_choice(mrq, "Its elegance")
        self.click_choice(mrq, "Its gracefulness")
        self.click_choice(mrq, "Its beauty")
        self.click_choice(rating, "4")
        self.click_submit(mentoring)

        # precondition - verifying 100% score achieved
        self.assertEqual(answer.get_attribute('value'), 'This is the answer')
        self._assert_feedback_showed(mcq, 0, "Great!", click_choice_result=True)
        self._assert_feedback_showed(
            mrq, 0, "This is something everyone has to like about this MRQ",
            click_choice_result=True
        )
        self._assert_feedback_showed(
            mrq, 1, "This is something everyone has to like about beauty",
            click_choice_result=True
        )
        self._assert_feedback_showed(mrq, 2, "This MRQ is indeed very graceful", click_choice_result=True)
        self._assert_feedback_showed(mrq, 3, "Nah, there aren't any!", click_choice_result=True)
        self._assert_feedback_showed(rating, 3, "I love good grades.", click_choice_result=True)
        self.assertTrue(messages.is_displayed())
        self.assertEqual(messages.text, "FEEDBACK\nAll Good")

        self._clear_filling(answer, mcq, mrq, rating)
        self._standard_filling(answer, mcq, mrq, rating)
        self.click_submit(mentoring)
        self._standard_checks(answer, mcq, mrq, rating, messages)

        # now, reload the page and make sure LATEST submission is loaded and feedback is shown
        mentoring = self.reload_student_view()
        answer, mcq, mrq, rating = self._get_controls(mentoring)
        messages = self._get_messages_element(mentoring)
        self._standard_checks(answer, mcq, mrq, rating, messages)

    def test_partial_mrq_is_not_completed(self):
        mentoring = self.load_scenario("feedback_persistence.xml")
        answer, mcq, mrq, rating = self._get_controls(mentoring)
        messages = self._get_messages_element(mentoring)

        answer.send_keys('This is the answer')
        self.click_choice(mcq, "Yes")
        # 1st, 3rd and 4th options, first three are correct, i.e. two mistakes: 2nd and 4th
        self.click_choice(mrq, "Its elegance")
        self.click_choice(mrq, "Its gracefulness")
        self.click_choice(rating, "4")
        self.click_submit(mentoring)

        def assert_state(answer, mcq, mrq, rating, messages):
            self.assertEqual(answer.get_attribute('value'), 'This is the answer')
            self._assert_feedback_showed(mcq, 0, "Great!", click_choice_result=True)
            self._assert_feedback_showed(
                mrq, 0, "This is something everyone has to like about this MRQ",
                click_choice_result=True
            )
            self._assert_feedback_showed(
                mrq, 1, "This is something everyone has to like about beauty",
                click_choice_result=True, success=False
            )
            self._assert_feedback_showed(mrq, 2, "This MRQ is indeed very graceful", click_choice_result=True)
            self._assert_feedback_showed(mrq, 3, "Nah, there aren't any!", click_choice_result=True)
            self._assert_feedback_showed(rating, 3, "I love good grades.", click_choice_result=True)
            self.assertTrue(messages.is_displayed())
            self.assertEqual(messages.text, "FEEDBACK\nNot done yet")

        assert_state(answer, mcq, mrq, rating, messages)

        # now, reload the page and make sure the same result is shown
        mentoring = self.reload_student_view()
        answer, mcq, mrq, rating = self._get_controls(mentoring)
        messages = self._get_messages_element(mentoring)
        assert_state(answer, mcq, mrq, rating, messages)

    @ddt.unpack
    @ddt.data(
        # MCQ with tips
        ("feedback_persistence_mcq_tips.xml", '.choice-tips'),
        # Like the above but instead of tips in MCQ
        # has a question level feedback. This feedback should also be suppressed.
        ("feedback_persistence_mcq_no_tips.xml", '.feedback')
    )
    def test_feedback_persistence_tips(self, scenario, tips_selector):
        # Tests whether feedback is hidden on reload.
        with mock.patch("problem_builder.mentoring.MentoringBlock.get_options") as patched_options:
            patched_options.return_value = {'pb_mcq_hide_previous_answer': True}
            mentoring = self.load_scenario(scenario)
            mcq = self._get_xblock(mentoring, "feedback_mcq_2")
            messages = mentoring.find_element_by_css_selector(tips_selector)
            self.assertFalse(messages.is_displayed())
            self.click_choice(mcq, "Yes")
            self.click_submit(mentoring)
            self.assertTrue(messages.is_displayed())
            mentoring = self.reload_student_view()
            messages = mentoring.find_element_by_css_selector(tips_selector)
            self.assertFalse(messages.is_displayed())
