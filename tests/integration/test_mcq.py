# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Harvard
#
# Authors:
#          Xavier Antoviaque <xavier@antoviaque.org>
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

from mentoring.test_base import MentoringBaseTest


# Classes ###########################################################


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

        self.assertEqual(messages.text, '')
        self.assertFalse(messages.find_elements_by_xpath('./*'))
        self.assertFalse(submit.is_enabled())

        mcq1_legend = mcq1.find_element_by_css_selector('legend')
        mcq2_legend = mcq2.find_element_by_css_selector('legend')
        self.assertEqual(mcq1_legend.text, 'QUESTION 1\nDo you like this MCQ?')
        self.assertEqual(mcq2_legend.text, 'QUESTION 2\nHow much do you rate this MCQ?')

        mcq1_choices = mcq1.find_elements_by_css_selector('.choices .choice label')
        mcq2_choices = mcq2.find_elements_by_css_selector('.rating .choice label')

        self.assertEqual(len(mcq1_choices), 3)
        self.assertEqual(len(mcq2_choices), 6)
        self.assertEqual(mcq1_choices[0].text, 'Yes')
        self.assertEqual(mcq1_choices[1].text, 'Maybe not')
        self.assertEqual(mcq1_choices[2].text, "I don't understand")
        self.assertEqual(mcq2_choices[0].text, '1')
        self.assertEqual(mcq2_choices[1].text, '2')
        self.assertEqual(mcq2_choices[2].text, '3')
        self.assertEqual(mcq2_choices[3].text, '4')
        self.assertEqual(mcq2_choices[4].text, '5')
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

        self.assertEqual(mcq1.find_element_by_css_selector(".feedback").text, 'Great!')
        self.assertEqual(mcq2.find_element_by_css_selector(".feedback").text, 'Will do better next time...')
        self.assertEqual(messages.text, '')
        self.assertFalse(messages.is_displayed())

        # Should show full completion when the right answers are selected
        self._selenium_bug_workaround_scroll_to(mcq1)
        mcq1_choices_input[0].click()
        mcq2_choices_input[3].click()
        self.assertTrue(submit.is_enabled())
        submit.click()
        self.wait_until_disabled(submit)

        self.assertEqual(mcq1.find_element_by_css_selector(".feedback").text, 'Great!')
        self.assertEqual(mcq2.find_element_by_css_selector(".feedback").text, 'I love good grades.')
        self.assertIn('All is good now...\nCongratulations!', messages.text)
        self.assertTrue(messages.is_displayed())

    def test_mcq_with_comments(self):
        mentoring = self.go_to_page('Mcq With Comments 1')
        mcq = mentoring.find_element_by_css_selector('fieldset.choices')
        messages = mentoring.find_element_by_css_selector('.messages')
        submit = mentoring.find_element_by_css_selector('.submit input.input-main')

        self.assertEqual(messages.text, '')
        self.assertFalse(messages.find_elements_by_xpath('./*'))
        self.assertFalse(submit.is_enabled())

        mcq_legend = mcq.find_element_by_css_selector('legend')
        self.assertEqual(mcq_legend.text, 'QUESTION\nWhat do you like in this MRQ?')

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
