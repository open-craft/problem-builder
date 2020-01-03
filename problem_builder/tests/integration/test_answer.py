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

from .base_test import MentoringBaseTest

# Classes ###########################################################


class AnswerBlockTest(MentoringBaseTest):
    def test_answer_edit(self):
        """
        Answers of same name should share value accross blocks
        """

        # Answer should initially be blank on all instances with the same answer name
        mentoring = self.go_to_page('Answer Edit 2')
        answer1_bis = mentoring.find_element_by_css_selector('textarea')
        answer1_readonly = mentoring.find_element_by_css_selector('blockquote.answer.read_only')
        self.assertEqual(answer1_bis.get_attribute('value'), '')
        self.assertEqual(answer1_readonly.text, 'No answer yet.')

        # Another answer with the same name
        mentoring = self.go_to_page('Answer Edit 1')

        # Check <html> child
        p = mentoring.find_element_by_css_selector('p')
        self.assertEqual(p.text, 'This should be displayed in the answer_edit scenario')

        # Initial unsubmitted text
        answer1 = mentoring.find_element_by_css_selector('textarea')
        self.assertEqual(answer1.text, '')

        # Submit is disabled for empty answer
        submit = mentoring.find_element_by_css_selector('.submit input.input-main')
        self.assertFalse(submit.is_enabled())

        # Filling in the answer enables the submit button
        answer1.send_keys('This is the answer')
        self.assertTrue(submit.is_enabled())
        submit.click()
        self.wait_until_disabled(submit)

        self.assertEqual(answer1.get_attribute('value'), 'This is the answer')

        # Modifying the answer re-enables submission
        answer1.send_keys('. It has a second statement.')
        self.assertTrue(submit.is_enabled())

        # Submitting a new answer overwrites the previous one
        submit.click()
        self.wait_until_disabled(submit)
        self.assertEqual(answer1.get_attribute('value'), 'This is the answer. It has a second statement.')

        # Answer content should show on a different instance with the same name
        mentoring = self.go_to_page('Answer Edit 2')
        answer1_bis = mentoring.find_element_by_css_selector('textarea')
        answer1_readonly = mentoring.find_element_by_css_selector('blockquote.answer.read_only')
        self.assertEqual(answer1_bis.get_attribute('value'), 'This is the answer. It has a second statement.')
        self.assertEqual(answer1_readonly.text, 'This is the answer. It has a second statement.')

    def test_answer_blank_read_only(self):
        """
        Read-only answers should not prevent completion when blank
        """
        # Check initial state
        mentoring = self.go_to_page('Answer Blank Read Only')
        answer = mentoring.find_element_by_css_selector('blockquote.answer.read_only')
        self.assertEqual(answer.text, 'No answer yet.')

        # Submit should allow to complete
        submit = mentoring.find_element_by_css_selector('.submit input.input-main')
        self.assertTrue(submit.is_enabled())
        submit.click()

        # Submit is disabled after submission
        self.wait_until_disabled(submit)
