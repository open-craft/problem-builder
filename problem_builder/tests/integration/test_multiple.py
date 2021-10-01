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

from .base_test import MentoringBaseTest


class MultipleBlockTest(MentoringBaseTest):
    """
    Test that multiple Problem Builder blocks can happily co-exist on a page.
    """
    default_css_selector = 'div.vertical'

    def test_answer_blocks(self, expect_answer=False):
        """
        Make sure that the JavaScript is working fine even though there are many blocks on the
        page. In this test we check the answer blocks.
        """
        vertical = self.go_to_page("Multiple Problem Builders")
        blocks = vertical.find_elements_by_css_selector('.mentoring')

        block_a = blocks[0]
        self.assertIn("First", block_a.text)
        block_b = blocks[1]
        self.assertIn("Recap", block_b.text)

        answer_input = block_a.find_element_by_css_selector("textarea")
        answer_output = block_b.find_element_by_css_selector("blockquote")

        if not expect_answer:
            self.assertEqual(answer_input.text, "")
            self.assertEqual(answer_output.text, "No answer yet.")
            answer_input.send_keys('Hello there')
            submit = block_a.find_element_by_css_selector('.submit input.input-main')
            self.assertTrue(submit.is_enabled())
            submit.click()
            self.wait_until_disabled(submit)
            self.test_answer_blocks(expect_answer=True)
        else:
            self.assertEqual(answer_input.text, 'Hello there')
            self.assertEqual(answer_output.text, 'Hello there')

    def test_mcq_mrq(self):
        """
        Make sure that the JavaScript is working fine even though there are many blocks on the
        page. In this test we check the MCQ and MRQ.
        """
        vertical = self.go_to_page("Multiple Problem Builders")
        blocks = vertical.find_elements_by_css_selector('.mentoring')

        block_c = blocks[2]
        self.assertIn("Third", block_c.text)
        block_d = blocks[3]
        self.assertIn("Fourth", block_d.text)

        # Ensure that both of the blocks C and D are both working simultaneously:
        for block in (block_c, block_d):
            submit = block.find_element_by_css_selector('.submit input.input-main')
            self.assertFalse(submit.is_enabled())
            block.find_elements_by_css_selector('.choices .choice label')[0].click()

            self.assertTrue(submit.is_enabled())
            submit.click()
            self.wait_until_disabled(submit)
