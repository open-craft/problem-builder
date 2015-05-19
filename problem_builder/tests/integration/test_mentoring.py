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

    def assert_status_icon_color(self, color):
        mentoring, controls = self.load_assessment_scenario('assessment_single.xml', {"max_attempts": 2})
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

    def _standard_filling(self, answer, mcq, mrq, rating):
        answer.send_keys('This is the answer')
        self.click_choice(mcq, "Yes")
        # 1st, 3rd and 4th options, first three are correct, i.e. two mistakes: 2nd and 4th
        self.click_choice(mrq, "Its elegance")
        self.click_choice(mrq, "Its gracefulness")
        self.click_choice(mrq, "Its bugs")
        self.click_choice(rating, "4")

    # mcq and rating can't be reset easily, but it's not required; listing them here to keep method signature similar
    def _clear_filling(self, answer, mcq, mrq, rating):      # pylint: disable=unused-argument
        answer.clear()
        for checkbox in mrq.find_elements_by_css_selector('.choice input'):
            if checkbox.is_selected():
                checkbox.click()

    def _standard_checks(self, answer, mcq, mrq, rating, messages):
        self.assertEqual(answer.get_attribute('value'), 'This is the answer')
        self._assert_feedback_showed(mcq, 0, "Great!")
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
        self._assert_feedback_showed(rating, 3, "I love good grades.", click_choice_result=True)
        self.assertTrue(messages.is_displayed())
        self.assertEqual(messages.text, "FEEDBACK\nNot done yet")

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
        mentoring = self.go_to_view("student_view")
        answer, mcq, mrq, rating = self._get_controls(mentoring)
        messages = self._get_messages_element(mentoring)
        submit = mentoring.find_element_by_css_selector('.submit input.input-main')

        self._standard_checks(answer, mcq, mrq, rating, messages)
        # after reloading submit is disabled...
        self.assertFalse(submit.is_enabled())

        # ...until some changes are done
        self.click_choice(mrq, "Its elegance")
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
        self._assert_feedback_showed(mcq, 0, "Great!")
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
        mentoring = self.go_to_view("student_view")
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
            self._assert_feedback_showed(mcq, 0, "Great!")
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
        mentoring = self.go_to_view("student_view")
        answer, mcq, mrq, rating = self._get_controls(mentoring)
        messages = self._get_messages_element(mentoring)
        assert_state(answer, mcq, mrq, rating, messages)
