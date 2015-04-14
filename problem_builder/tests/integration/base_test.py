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

from xblock.fields import String
from xblockutils.base_test import SeleniumBaseTest

# Studio adds a url_name property to each XBlock but Workbench doesn't.
# Since we rely on it, we need to mock url_name support so it can be set via XML and
# accessed like a normal field.
from problem_builder import MentoringBlock
MentoringBlock.url_name = String()


class MentoringBaseTest(SeleniumBaseTest):
    module_name = __name__
    default_css_selector = 'div.mentoring'

    def popup_check(self, mentoring, item_feedbacks, prefix='', do_submit=True):

        submit = mentoring.find_element_by_css_selector('.submit input.input-main')

        for index, expected_feedback in enumerate(item_feedbacks):
            choice_wrapper = mentoring.find_elements_by_css_selector(prefix + " .choice")[index]
            if do_submit:
                # clicking on actual radio button
                choice_wrapper.find_element_by_css_selector(".choice-selector input").click()
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


class MentoringAssessmentBaseTest(MentoringBaseTest):
    @staticmethod
    def question_text(number):
        if number:
            return "Question %s" % number
        else:
            return "Question"

    def go_to_assessment(self, page):
        """ Navigates to assessment page """
        mentoring = self.go_to_page(page)

        class Namespace(object):
            pass

        controls = Namespace()

        controls.submit = mentoring.find_element_by_css_selector("input.input-main")
        controls.next_question = mentoring.find_element_by_css_selector("input.input-next")
        controls.review = mentoring.find_element_by_css_selector("input.input-review")
        controls.try_again = mentoring.find_element_by_css_selector("input.input-try-again")
        controls.review_link = mentoring.find_element_by_css_selector(".review-link a")

        return mentoring, controls

    def expect_question_visible(self, number, mentoring):
        question_text = self.question_text(number)
        self.wait_until_text_in(self.question_text(number), mentoring)
        question_div = None
        for xblock_div in mentoring.find_elements_by_css_selector('div.xblock-v1'):
            header_text = xblock_div.find_elements_by_css_selector('h3.question-title')
            if header_text and question_text in header_text[0].text:
                question_div = xblock_div
                self.assertTrue(xblock_div.is_displayed())
            elif header_text:
                self.assertFalse(xblock_div.is_displayed())
            # else this is an HTML block or something else, not a question step

        self.assertIsNotNone(question_div)
        return question_div


class GetChoices(object):
    """ Helper class for interacting with MCQ options """
    def __init__(self, question, selector=".choices"):
        self._mcq = question.find_element_by_css_selector(selector)

    @property
    def text(self):
        return self._mcq.text

    @property
    def state(self):
        return {
            choice.text: choice.find_element_by_css_selector("input").is_selected()
            for choice in self._mcq.find_elements_by_css_selector(".choice")}

    def select(self, text):
        choice_wrapper = self.get_option_element(text)
        choice_wrapper.find_element_by_css_selector("input").click()

    def get_option_element(self, text):
        for choice in self._mcq.find_elements_by_css_selector(".choice"):
            if choice.text == text:
                return choice
        raise AssertionError("Expected selectable item present: {}".format(text))
