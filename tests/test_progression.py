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

class MentoringProgressionTest(MentoringBaseTest):

    def assert_warning(self, warning_dom, link_href):
        """
        Check that the provided DOM element is a progression warning, and includes a link with a href
        pointing to `link_href`
        """
        self.assertEqual(warning_dom.text, 'You need to complete the following step before attempting this step.')
        warning_link = warning_dom.find_element_by_xpath('./*')
        link_href = 'http://localhost:8081{}'.format(link_href)
        self.assertEqual(warning_link.get_attribute('href'), link_href)

    def test_progression(self):
        """
        Mentoring blocks after the current step in the workflow should redirect user to current step
        """
        # Initial - Step 1 ok, steps 2&3 redirect to step 1
        mentoring = self.go_to_page('Progression 1')
        self.assertFalse(mentoring.find_elements_by_css_selector('.warning'))

        mentoring = self.go_to_page('Progression 2')
        warning = mentoring.find_element_by_css_selector('.warning')
        self.assert_warning(warning, '/jump_to_id/mentoring_first')

        mentoring = self.go_to_page('Progression 3')
        warning = mentoring.find_element_by_css_selector('.warning')
        self.assert_warning(warning, '/jump_to_id/mentoring_first')

        # Submit step 1 without completing it - no change should be registered
        mentoring = self.go_to_page('Progression 1')
        submit = mentoring.find_element_by_css_selector('input.submit')
        submit.click()
        self.assertFalse(mentoring.find_elements_by_css_selector('.warning'))

        progress = mentoring.find_element_by_css_selector('.progress > .indicator')
        self.assertEqual(progress.text, '(Not completed)')
        self.assertFalse(progress.find_elements_by_xpath('./*'))

        mentoring = self.go_to_page('Progression 2')
        warning = mentoring.find_element_by_css_selector('.warning')
        self.assert_warning(warning, '/jump_to_id/mentoring_first')

        mentoring = self.go_to_page('Progression 3')
        warning = mentoring.find_element_by_css_selector('.warning')
        self.assert_warning(warning, '/jump_to_id/mentoring_first')

        # Should be impossible to complete step 2
        mentoring = self.go_to_page('Progression 2')
        answer = mentoring.find_element_by_css_selector('textarea')
        answer.send_keys('This is the answer')
        submit = mentoring.find_element_by_css_selector('input.submit')
        submit.click()

        progress = mentoring.find_element_by_css_selector('.progress > .indicator')
        self.assertEqual(progress.text, '(Not completed)')
        self.assertFalse(progress.find_elements_by_xpath('./*'))

        mentoring = self.go_to_page('Progression 2')
        warning = mentoring.find_element_by_css_selector('.warning')
        self.assert_warning(warning, '/jump_to_id/mentoring_first')

        mentoring = self.go_to_page('Progression 3')
        warning = mentoring.find_element_by_css_selector('.warning')
        self.assert_warning(warning, '/jump_to_id/mentoring_first')

        # Complete step 1 - now only step 3 should redirect, and to step 2
        mentoring = self.go_to_page('Progression 1')
        answer = mentoring.find_element_by_css_selector('textarea')
        answer.send_keys('This is the answer')
        submit = mentoring.find_element_by_css_selector('input.submit')
        submit.click()
        self.assertFalse(mentoring.find_elements_by_css_selector('.warning'))

        progress = mentoring.find_element_by_css_selector('.progress > .indicator')
        self.assertEqual(progress.text, '')
        self.assertTrue(progress.find_elements_by_css_selector('img'))

        mentoring = self.go_to_page('Progression 2')
        self.assertFalse(mentoring.find_elements_by_css_selector('.warning'))

        mentoring = self.go_to_page('Progression 3')
        warning = mentoring.find_element_by_css_selector('.warning')
        self.assert_warning(warning, '/jump_to_id/progression_2')

        # Complete step 2 - no more warnings anywhere
        mentoring = self.go_to_page('Progression 2')
        submit = mentoring.find_element_by_css_selector('input.submit')
        submit.click() # Already filled the textarea in previous step

        progress = mentoring.find_element_by_css_selector('.progress > .indicator')
        self.assertEqual(progress.text, '')
        self.assertTrue(progress.find_elements_by_css_selector('img'))

        mentoring = self.go_to_page('Progression 1')
        self.assertFalse(mentoring.find_elements_by_css_selector('.warning'))

        mentoring = self.go_to_page('Progression 2')
        self.assertFalse(mentoring.find_elements_by_css_selector('.warning'))

        mentoring = self.go_to_page('Progression 3')
        self.assertFalse(mentoring.find_elements_by_css_selector('.warning'))

        # Should be able to complete step 3 too now
        mentoring = self.go_to_page('Progression 3')
        answer = mentoring.find_element_by_css_selector('textarea')
        answer.send_keys('This is the answer')
        submit = mentoring.find_element_by_css_selector('input.submit')
        submit.click()

        progress = mentoring.find_element_by_css_selector('.progress > .indicator')
        self.assertEqual(progress.text, '')
        self.assertTrue(progress.find_elements_by_css_selector('img'))

