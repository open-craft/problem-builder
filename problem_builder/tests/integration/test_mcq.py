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

import ddt
from mock import patch, Mock

from problem_builder.mentoring import MentoringBlock
from .base_test import MentoringBaseTest


# Classes ###########################################################


@ddt.ddt
class MCQBlockTest(MentoringBaseTest):

    def _selenium_bug_workaround_scroll_to(self, mcq_legend):
        """Workaround for selenium bug:

        Some version of Selenium has a bug that prevents scrolling
        to radiobuttons before being clicked. The click not taking
        place, when it's outside the view.

        Since the bug does not affect other content, asking Selenium
        to click on the legend first, will properly scroll it.
        """
        mcq_legend.click()

    def _get_inputs(self, choices):
        return [choice.find_element_by_css_selector('input') for choice in choices]

    def assert_messages_empty(self, messages):
        self.assertEqual(messages.text, '')
        self.assertFalse(messages.find_elements_by_xpath('./*'))

    def test_mcq_choices_rating(self):
        """
        Mentoring MCQ should display tips according to user choice
        """
        # Initial MCQ status
        mentoring = self.go_to_page('Mcq 1')
        mcq1 = mentoring.find_element_by_css_selector('fieldset.choices')
        mcq2 = mentoring.find_element_by_css_selector('fieldset.rating')
        messages = mentoring.find_element_by_css_selector('.messages')
        submit = mentoring.find_element_by_css_selector('.submit input.input-main')

        self.assert_messages_empty(messages)
        self.assertFalse(submit.is_enabled())

        mcq1_legend = mcq1.find_element_by_css_selector('legend')
        mcq2_legend = mcq2.find_element_by_css_selector('legend')
        self.assertEqual(mcq1_legend.text, 'Question 1\nDo you like this MCQ?')
        self.assertEqual(mcq2_legend.text, 'Question 2\nHow do you rate this MCQ?')

        mcq1_choices = mcq1.find_elements_by_css_selector('.choices .choice label')
        mcq2_choices = mcq2.find_elements_by_css_selector('.rating .choice label')

        self.assertEqual(len(mcq1_choices), 3)
        self.assertEqual(len(mcq2_choices), 6)
        self.assertEqual(mcq1_choices[0].text, 'Yes')
        self.assertEqual(mcq1_choices[1].text, 'Maybe not')
        self.assertEqual(mcq1_choices[2].text, "I don't understand")
        self.assertEqual(mcq2_choices[0].text, '1 - Not good at all')
        self.assertEqual(mcq2_choices[1].text, '2')
        self.assertEqual(mcq2_choices[2].text, '3')
        self.assertEqual(mcq2_choices[3].text, '4')
        self.assertEqual(mcq2_choices[4].text, '5 - Extremely good')
        self.assertEqual(mcq2_choices[5].text, "I don't want to rate it")

        mcq1_choices_input = self._get_inputs(mcq1_choices)
        mcq2_choices_input = self._get_inputs(mcq2_choices)

        self.assertEqual(mcq1_choices_input[0].get_attribute('value'), 'yes')
        self.assertEqual(mcq1_choices_input[1].get_attribute('value'), 'maybenot')
        self.assertEqual(mcq1_choices_input[2].get_attribute('value'), 'understand')
        self.assertEqual(mcq2_choices_input[0].get_attribute('value'), '1')
        self.assertEqual(mcq2_choices_input[1].get_attribute('value'), '2')
        self.assertEqual(mcq2_choices_input[2].get_attribute('value'), '3')
        self.assertEqual(mcq2_choices_input[3].get_attribute('value'), '4')
        self.assertEqual(mcq2_choices_input[4].get_attribute('value'), '5')
        self.assertEqual(mcq2_choices_input[5].get_attribute('value'), 'notwant')

        # Submit button disabled without selecting anything
        self.assertFalse(submit.is_enabled())

        # Submit button stays disabled when there are unfinished mcqs
        self._selenium_bug_workaround_scroll_to(mcq1)
        mcq1_choices_input[1].click()
        self.assertFalse(submit.is_enabled())

        # Should not show full completion message when wrong answers are selected
        self._selenium_bug_workaround_scroll_to(mcq1)
        mcq1_choices_input[0].click()
        mcq2_choices_input[2].click()
        self.assertTrue(submit.is_enabled())
        submit.click()
        self.wait_until_disabled(submit)

        mcq1_tips = mcq1.find_element_by_css_selector(".choice-tips .tip p")
        mcq2_tips = mcq2.find_element_by_css_selector(".choice-tips .tip p")

        self.assertEqual(mcq1_tips.text, 'Great!')
        self.assertTrue(mcq1_tips.is_displayed())
        self.assertEqual(mcq2_tips.text, 'Will do better next time...')
        self.assertTrue(mcq2_tips.is_displayed())
        self.assertEqual(messages.text, '')
        self.assertFalse(messages.is_displayed())

        # Should show full completion when the right answers are selected
        self._selenium_bug_workaround_scroll_to(mcq1)
        mcq1_choices_input[0].click()
        mcq2_choices_input[3].click()
        self.assertTrue(submit.is_enabled())
        submit.click()
        self.wait_until_disabled(submit)

        mcq1_tips = mcq1.find_element_by_css_selector(".choice-tips .tip p")
        mcq2_tips = mcq2.find_element_by_css_selector(".choice-tips .tip p")

        self.assertEqual(mcq1_tips.text, 'Great!')
        self.assertTrue(mcq1_tips.is_displayed())
        self.assertEqual(mcq2_tips.text, 'I love good grades.')
        self.assertTrue(mcq2_tips.is_displayed())
        self.assertIn('All is good now...\nCongratulations!', messages.text)
        self.assertTrue(messages.is_displayed())

        # The choice tip containers should have the with-tips class.
        mcq1_tip_containers = mcq1.find_elements_by_css_selector('.choice-tips-container.with-tips')
        mcq2_tip_containers = mcq2.find_elements_by_css_selector('.choice-tips-container.with-tips')
        self.assertEqual(len(mcq1_tip_containers), 3)
        self.assertEqual(len(mcq2_tip_containers), 6)

        # Clicking outside the tips should hide the tips and clear the with-tips class.
        mcq1.find_element_by_css_selector('.mentoring .question-title').click()
        mcq2.find_element_by_css_selector('.mentoring .question-title').click()
        mcq1_tip_containers = mcq1.find_elements_by_css_selector('.choice-tips-container.with-tips')
        mcq2_tip_containers = mcq2.find_elements_by_css_selector('.choice-tips-container.with-tips')
        self.assertEqual(len(mcq1_tip_containers), 0)
        self.assertEqual(len(mcq2_tip_containers), 0)
        self.assertFalse(mcq1_tips.is_displayed())
        self.assertFalse(mcq2_tips.is_displayed())

    def test_mcq_with_comments(self):
        mentoring = self.go_to_page('Mcq With Comments 1')
        mcq = mentoring.find_element_by_css_selector('fieldset.choices')
        messages = mentoring.find_element_by_css_selector('.messages')
        submit = mentoring.find_element_by_css_selector('.submit input.input-main')

        self.assertEqual(messages.text, '')
        self.assertFalse(messages.find_elements_by_xpath('./*'))
        self.assertFalse(submit.is_enabled())

        mcq_legend = mcq.find_element_by_css_selector('legend')
        self.assertEqual(mcq_legend.text, 'Question\nWhat do you like in this MRQ?')

        mcq_choices = mcq.find_elements_by_css_selector('.choices .choice label')

        self.assertEqual(len(mcq_choices), 4)
        self.assertEqual(mcq_choices[0].text, 'Its elegance')
        self.assertEqual(mcq_choices[1].text, 'Its beauty')
        self.assertEqual(mcq_choices[2].text, "Its gracefulness")
        self.assertEqual(mcq_choices[3].text, "Its bugs")

        mcq_choices_input = self._get_inputs(mcq_choices)
        self.assertEqual(mcq_choices_input[0].get_attribute('value'), 'elegance')
        self.assertEqual(mcq_choices_input[1].get_attribute('value'), 'beauty')
        self.assertEqual(mcq_choices_input[2].get_attribute('value'), 'gracefulness')
        self.assertEqual(mcq_choices_input[3].get_attribute('value'), 'bugs')

    def test_mcq_feedback_popups(self):
        mentoring = self.go_to_page('Mcq With Comments 1')
        choices_list = mentoring.find_element_by_css_selector(".choices-list")

        item_feedbacks = [
            "This is something everyone has to like about this MRQ",
            "This is something everyone has to like about beauty",
            "This MRQ is indeed very graceful",
            "Nah, there isn\\'t any!"
        ]
        submit = mentoring.find_element_by_css_selector('.submit input.input-main')

        for index, expected_feedback in enumerate(item_feedbacks):
            choice_wrapper = choices_list.find_elements_by_css_selector(".choice")[index]
            choice_wrapper.find_element_by_css_selector(".choice-selector").click()  # clicking on actual radio button
            submit.click()
            self.wait_until_disabled(submit)
            item_feedback_icon = choice_wrapper.find_element_by_css_selector(".choice-result")
            choice_wrapper.click()
            item_feedback_icon.click()  # clicking on item feedback icon
            item_feedback_popup = choice_wrapper.find_element_by_css_selector(".choice-tips")
            self.assertTrue(item_feedback_popup.is_displayed())
            self.assertEqual(item_feedback_popup.text, expected_feedback)

            item_feedback_popup.click()
            self.assertTrue(item_feedback_popup.is_displayed())

            mentoring.click()
            self.assertFalse(item_feedback_popup.is_displayed())

    def _get_questionnaire_options(self, questionnaire):
        result = []
        # this could be a list comprehension, but a bit complicated one - hence explicit loop
        for choice_wrapper in questionnaire.find_elements_by_css_selector(".choice"):
            choice_label = choice_wrapper.find_element_by_css_selector("label .choice-text")
            result.append(choice_label.get_attribute('innerHTML'))

        return result

    @ddt.data(
        'Mrq With Html Choices',
        'Mcq With Html Choices'
    )
    def test_questionnaire_html_choices(self, page):
        mentoring = self.go_to_page(page)
        choices_list = mentoring.find_element_by_css_selector(".choices-list")
        messages = mentoring.find_element_by_css_selector('.messages')

        expected_options = [
            "<strong>Its elegance</strong>",
            "<em>Its beauty</em>",
            "<strong>Its gracefulness</strong>",
            '<span style="font-color:red">Its bugs</span>'
        ]

        options = self._get_questionnaire_options(choices_list)
        self.assertEqual(expected_options, options)

        self.assert_messages_empty(messages)

        submit = mentoring.find_element_by_css_selector('.submit input.input-main')
        self.assertFalse(submit.is_enabled())

        inputs = choices_list.find_elements_by_css_selector('input.choice-selector')
        self._selenium_bug_workaround_scroll_to(choices_list)
        inputs[0].click()
        inputs[1].click()
        inputs[2].click()

        self.assertTrue(submit.is_enabled())
        submit.click()
        self.wait_until_disabled(submit)

        self.assertIn('Congratulations!', messages.text)


@patch.object(MentoringBlock, 'get_theme', Mock(return_value={'package': 'problem_builder',
                                                              'locations': ['public/themes/lms.css']}))
class MCQBlockAprosThemeTest(MCQBlockTest):
    """
    Test MRQ/MCQ questions without the LMS theme which is on by default.
    """
    pass
