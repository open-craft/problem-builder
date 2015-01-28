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
import urllib2
from .base_test import MentoringBaseTest


# Classes ###########################################################


@ddt.ddt
class AnswerBlockTest(MentoringBaseTest):
    """
    Test mentoring's data export tool.
    """
    default_css_selector = 'body'

    def go_to_page_as_student(self, page_name, student_id):
        """
        Navigate to the page `page_name`, as listed on the workbench home
        but override the student_id used
        """
        self.browser.get(self.live_server_url)
        href = self.browser.find_element_by_link_text(page_name).get_attribute("href")
        href += "?student={}".format(student_id)
        self.browser.get(href)
        block = self.browser.find_element_by_css_selector(self._default_css_selector)
        return block

    def click_submit_button(self, page, mentoring_block_index):
        """
        Click on one of the submit buttons on the page
        """
        mentoring_div = page.find_elements_by_css_selector('div.mentoring')[mentoring_block_index]
        submit = mentoring_div.find_element_by_css_selector('.submit .input-main')
        self.assertTrue(submit.is_enabled())
        submit.click()
        self.wait_until_disabled(submit)

    @ddt.data(
        # student submissions, expected CSV text
        (
            [
                ("student10", "Essay1", "Essay2", "Essay3"),
                ("student20", "I didn't answer the last two questions", None, None),
            ],
            (
                u"student_id,goal,inspired,meaning\r\n"
                "student10,Essay1,Essay2,Essay3\r\n"
                "student20,I didn't answer the last two questions,,\r\n"
            )
        ),
    )
    @ddt.unpack
    def test_data_export_edit(self, submissions, expected_csv):
        """
        Have students submit answers, then run an export and validate the output
        """
        for student_id, answer1, answer2, answer3 in submissions:
            page = self.go_to_page_as_student('Data Export', student_id)

            answer1_field = page.find_element_by_css_selector('div[data-name=goal] textarea')
            self.assertEqual(answer1_field.text, '')
            answer1_field.send_keys(answer1)
            self.click_submit_button(page, 0)

            if answer2:
                answer2_field = page.find_element_by_css_selector('div[data-name=inspired] textarea')
                self.assertEqual(answer2_field.text, '')
                answer2_field.send_keys(answer2)
                self.click_submit_button(page, 1)
                mentoring_div = page.find_elements_by_css_selector('div.mentoring')[1]
                next = mentoring_div.find_element_by_css_selector('.submit .input-next')
                next.click()
                self.wait_until_disabled(next)

            if answer3:
                answer3_field = page.find_element_by_css_selector('div[data-name=meaning] textarea')
                self.assertEqual(answer3_field.text, '')
                answer3_field.send_keys(answer3)
                self.click_submit_button(page, 1)

        export_div = page.find_element_by_css_selector('.mentoring-dataexport')
        self.assertIn("for the 3 answers in this course", export_div.text)

        # Now "click" on the export link:
        download_url = self.browser.find_element_by_link_text('Download CSV Export').get_attribute("href")
        response = urllib2.urlopen(download_url)
        headers = response.info()
        self.assertTrue(headers['Content-Type'].startswith('text/csv'))
        csv_data = response.read()
        self.assertEqual(csv_data, expected_csv)
