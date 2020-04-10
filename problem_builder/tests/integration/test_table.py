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

from unittest.mock import patch

from workbench.runtime import WorkbenchRuntime

from .base_test import MentoringBaseTest

# Classes ###########################################################


class MentoringTableBlockTest(MentoringBaseTest):

    def test_mentoring_table(self):
        # Initially, the table should be blank, with just the titles
        table = self.go_to_page('Table 2', css_selector='.mentoring-table')
        headers = table.find_elements_by_css_selector('th')
        self.assertEqual(len(headers), 2)
        self.assertEqual(headers[0].text, 'Header Test 1')
        self.assertEqual(headers[1].text, 'Header Test 2')

        rows = table.find_elements_by_css_selector('td')
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].text, 'No answer yet.')
        self.assertEqual(rows[1].text, 'No answer yet.')

        # Fill the answers - they should appear in the table
        mentoring = self.go_to_page('Table 1')
        answers = mentoring.find_elements_by_css_selector('textarea')
        answers[0].send_keys('This is the answer #1')
        answers[1].send_keys('This is the answer #2')
        submit = mentoring.find_element_by_css_selector('.submit input.input-main')
        submit.click()
        self.wait_until_disabled(submit)

        table = self.go_to_page('Table 2', css_selector='.mentoring-table')
        rows = table.find_elements_by_css_selector('td')
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].text, 'This is the answer #1')
        self.assertEqual(rows[1].text, 'This is the answer #2')

        # Ensure that table block makes an effort to translate URLs in column headers
        link_template = "<a href='http://www.test.com'>{}</a> in a column header."
        original_contents = link_template.format('Link')
        updated_contents = link_template.format('Updated link')

        with patch.object(WorkbenchRuntime, 'replace_jump_to_id_urls', create=True) as patched_method:
            patched_method.return_value = updated_contents

            table = self.go_to_page('Table 3', css_selector='.mentoring-table')
            patched_method.assert_called_once_with(original_contents)
            link = table.find_element_by_css_selector('a')
            self.assertEquals(link.text, 'Updated link')
