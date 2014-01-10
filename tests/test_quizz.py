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

import time

from mentoring.test_base import MentoringBaseTest


# Classes ###########################################################

class QuizzBlockTest(MentoringBaseTest):

    def test_quizz_choices_rating(self):
        """
        Mentoring quizz should display tips according to user choice
        """
        # Initial quizzes status
        mentoring = self.go_to_page('Quizz 1')
        quizz1 = mentoring.find_element_by_css_selector('fieldset.choices')
        quizz2 = mentoring.find_element_by_css_selector('fieldset.rating')
        messages = mentoring.find_element_by_css_selector('.messages')
        progress = mentoring.find_element_by_css_selector('.progress > .indicator')

        self.assertEqual(messages.text, '')
        self.assertFalse(messages.find_elements_by_xpath('./*'))
        self.assertEqual(progress.text, '(Not completed)')
        self.assertFalse(progress.find_elements_by_xpath('./*'))

        quizz1_legend = quizz1.find_element_by_css_selector('legend')
        quizz2_legend = quizz2.find_element_by_css_selector('legend')
        self.assertEqual(quizz1_legend.text, 'Do you like this quizz?')
        self.assertEqual(quizz2_legend.text, 'How much do you rate this quizz?')

        quizz1_choices = quizz1.find_elements_by_css_selector('.choices .choice label')
        quizz2_choices = quizz2.find_elements_by_css_selector('.choices .choice label')

        self.assertEqual(len(quizz1_choices), 3)
        self.assertEqual(len(quizz2_choices), 6)
        self.assertEqual(quizz1_choices[0].text, 'Yes')
        self.assertEqual(quizz1_choices[1].text, 'Maybe not')
        self.assertEqual(quizz1_choices[2].text, "I don't understand")
        self.assertEqual(quizz2_choices[0].text, '1')
        self.assertEqual(quizz2_choices[1].text, '2')
        self.assertEqual(quizz2_choices[2].text, '3')
        self.assertEqual(quizz2_choices[3].text, '4')
        self.assertEqual(quizz2_choices[4].text, '5')
        self.assertEqual(quizz2_choices[5].text, "I don't want to rate it")

        quizz1_choices_input = [
            quizz1_choices[0].find_element_by_css_selector('input'),
            quizz1_choices[1].find_element_by_css_selector('input'),
            quizz1_choices[2].find_element_by_css_selector('input'),
        ]
        quizz2_choices_input = [
            quizz2_choices[0].find_element_by_css_selector('input'),
            quizz2_choices[1].find_element_by_css_selector('input'),
            quizz2_choices[2].find_element_by_css_selector('input'),
            quizz2_choices[3].find_element_by_css_selector('input'),
            quizz2_choices[4].find_element_by_css_selector('input'),
            quizz2_choices[5].find_element_by_css_selector('input'),
        ]
        self.assertEqual(quizz1_choices_input[0].get_attribute('value'), 'yes')
        self.assertEqual(quizz1_choices_input[1].get_attribute('value'), 'maybenot')
        self.assertEqual(quizz1_choices_input[2].get_attribute('value'), 'understand')
        self.assertEqual(quizz2_choices_input[0].get_attribute('value'), '1')
        self.assertEqual(quizz2_choices_input[1].get_attribute('value'), '2')
        self.assertEqual(quizz2_choices_input[2].get_attribute('value'), '3')
        self.assertEqual(quizz2_choices_input[3].get_attribute('value'), '4')
        self.assertEqual(quizz2_choices_input[4].get_attribute('value'), '5')
        self.assertEqual(quizz2_choices_input[5].get_attribute('value'), 'notwant')

        # Submit without selecting anything
        submit = mentoring.find_element_by_css_selector('input.submit')
        submit.click()

        tips = messages.find_elements_by_xpath('./*')
        self.assertEqual(len(tips), 2)
        self.assertEqual(tips[0].text, 'To the question "Do you like this quizz?", you have not provided an answer.')
        self.assertEqual(tips[1].text, 'To the question "How much do you rate this quizz?", you have not provided an answer.')
        self.assertEqual(progress.text, '(Not completed)')
        self.assertFalse(progress.find_elements_by_xpath('./*'))

        # Select only one option
        quizz1_choices_input[1].click()
        submit.click()

        time.sleep(1)
        tips = messages.find_elements_by_xpath('./*')
        self.assertEqual(len(tips), 2)
        self.assertEqual(tips[0].text, 'To the question "Do you like this quizz?", you answered "Maybe not".\nAh, damn.')
        self.assertEqual(tips[1].text, 'To the question "How much do you rate this quizz?", you have not provided an answer.')
        self.assertEqual(progress.text, '(Not completed)')
        self.assertFalse(progress.find_elements_by_xpath('./*'))

        # One with only display tip, one with reject tip - should not complete
        quizz1_choices_input[0].click()
        quizz2_choices_input[2].click()
        submit.click()

        time.sleep(1)
        tips = messages.find_elements_by_xpath('./*')
        self.assertEqual(len(tips), 2)
        self.assertEqual(tips[0].text, 'To the question "Do you like this quizz?", you answered "Yes".\nGreat!')
        self.assertEqual(tips[1].text, 'To the question "How much do you rate this quizz?", you answered "3".\nWill do better next time...')
        self.assertEqual(progress.text, '(Not completed)')
        self.assertFalse(progress.find_elements_by_xpath('./*'))

        # Only display tips, to allow to complete
        quizz1_choices_input[0].click()
        quizz2_choices_input[3].click()
        submit.click()

        time.sleep(1)
        tips = messages.find_elements_by_xpath('./*')
        self.assertEqual(len(tips), 3)
        self.assertEqual(tips[0].text, 'To the question "Do you like this quizz?", you answered "Yes".\nGreat!')
        self.assertEqual(tips[1].text, 'To the question "How much do you rate this quizz?", you answered "4".\nI love good grades.')
        self.assertEqual(tips[2].text, 'Congratulations!\nAll is good now...') # Includes child <html>
        self.assertEqual(progress.text, '')
        self.assertTrue(progress.find_elements_by_css_selector('img'))

