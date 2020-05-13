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

from unittest import mock
from xblock.fields import String
from xblockutils.base_test import SeleniumBaseTest, SeleniumXBlockTest
from xblockutils.resources import ResourceLoader

# Studio adds a url_name property to each XBlock but Workbench doesn't.
# Since we rely on it, we need to mock url_name support so it can be set via XML and
# accessed like a normal field.
from problem_builder.mentoring import MentoringBlock

MentoringBlock.url_name = String()

loader = ResourceLoader(__name__)

CORRECT, INCORRECT, PARTIAL = "correct", "incorrect", "partially-correct"


class PopupCheckMixin:
    """
    Code used by MentoringBaseTest and MentoringAssessmentBaseTest
    """
    def popup_check(self, mentoring, item_feedbacks, prefix='', do_submit=True):

        submit = mentoring.find_element_by_css_selector('.submit input.input-main')

        for index, expected_feedback in enumerate(item_feedbacks):

            self.wait_until_exists(prefix + " .choice")
            choice_wrapper = mentoring.find_elements_by_css_selector(prefix + " .choice")[index]
            if do_submit:
                # clicking on actual radio button
                self.wait_until_exists(".choice-selector input")
                choice_wrapper.find_element_by_css_selector(".choice-selector input").click()
                submit.click()
            self.wait_until_disabled(submit)
            self.wait_until_exists(".choice-result")
            item_feedback_icon = choice_wrapper.find_element_by_css_selector(".choice-result")
            self.wait_until_clickable(item_feedback_icon)
            item_feedback_icon.click()  # clicking on item feedback icon
            self.wait_until_exists(".choice-tips")
            item_feedback_popup = choice_wrapper.find_element_by_css_selector(".choice-tips")
            self.assertTrue(item_feedback_popup.is_displayed())
            self.assertEqual(item_feedback_popup.text, expected_feedback)

            self.wait_until_clickable(item_feedback_popup)
            item_feedback_popup.click()
            self.wait_until_visible(item_feedback_popup)
            self.assertTrue(item_feedback_popup.is_displayed())

            mentoring.find_element_by_css_selector('.title').click()
            self.wait_until_hidden(item_feedback_popup)
            self.assertFalse(item_feedback_popup.is_displayed())


class ProblemBuilderBaseTest(SeleniumXBlockTest, PopupCheckMixin):
    """
    The new base class for integration tests.
    Scenarios can be loaded and edited on the fly.
    """
    default_css_selector = 'div.mentoring'

    def load_scenario(self, xml_file, params=None, load_immediately=True):
        """
        Given the name of an XML file in the xml_templates folder, load it into the workbench.
        """
        params = params or {}
        scenario = loader.render_django_template("xml_templates/{}".format(xml_file), params)
        self.set_scenario_xml(scenario)
        if load_immediately:
            return self.go_to_view("student_view")

    def go_to_view(self, view_name):
        """ Eliminate errors that come from the Workbench banner overlapping elements """
        element = super(ProblemBuilderBaseTest, self).go_to_view(view_name)
        self.browser.execute_script('document.querySelectorAll("header.banner")[0].style.display="none";')
        return element

    def wait_for_init(self):
        """ Wait for the scenario to initialize """
        self.wait_until_hidden(self.browser.find_element_by_css_selector('.messages'))

    def reload_page(self):
        """
        Reload current page.
        """
        self.browser.execute_script("$(document).html(' ');")
        return self.go_to_view("student_view")

    @property
    def checkmark(self):
        return self.browser.find_element_by_css_selector('.submit-result')

    @property
    def submit_button(self):
        return self.browser.find_element_by_css_selector('.submit input.input-main')

    def click_submit(self, mentoring):
        """ Click the submit button and wait for the response """
        submit = mentoring.find_element_by_css_selector('.submit input.input-main')
        self.assertTrue(submit.is_displayed())
        self.assertTrue(submit.is_enabled())
        submit.click()
        self.wait_until_disabled(submit)

    def click_choice(self, container, choice_text):
        """ Click on the choice label with the specified text """
        for label in container.find_elements_by_css_selector('.choice label'):
            if choice_text in label.text:
                label.click()
                break

    def expect_checkmark_visible(self, visible):
        if visible:
            self.wait_until_visible(self.checkmark)
        else:
            self.wait_until_hidden(self.checkmark)
        self.assertEqual(self.checkmark.is_displayed(), visible)

    def expect_submit_enabled(self, enabled):
        if enabled:
            self.wait_until_clickable(self.submit_button)
        else:
            self.wait_until_disabled(self.submit_button)
        self.assertEqual(self.submit_button.is_enabled(), enabled)


class MentoringBaseTest(SeleniumBaseTest, PopupCheckMixin):
    module_name = __name__
    default_css_selector = 'div.mentoring'

    __asides_patch = None

    def go_to_page(self, page_title, **kwargs):
        """ Eliminate errors that come from the Workbench banner overlapping elements """
        element = super(MentoringBaseTest, self).go_to_page(page_title, **kwargs)
        self.browser.execute_script('document.querySelectorAll("header.banner")[0].style.display="none";')
        return element

    @classmethod
    def setUpClass(cls):
        super(MentoringBaseTest, cls).setUpClass()
        cls.__asides_patch = mock.patch(
            "workbench.runtime.WorkbenchRuntime.applicable_aside_types",
            mock.Mock(return_value=[])
        )
        cls.__asides_patch.start()

    @classmethod
    def tearDownClass(cls):
        cls.__asides_patch.stop()
        super(MentoringBaseTest, cls).tearDownClass()


class MentoringAssessmentBaseTest(ProblemBuilderBaseTest):
    """
    Base class for tests of assessment mode
    """
    @staticmethod
    def question_text(number):
        if number:
            return "Question %s" % number
        else:
            return "Question"

    def load_assessment_scenario(self, xml_file, params=None):
        """ Loads an assessment scenario from an XML template """
        params = params or {}
        scenario = loader.render_django_template("xml_templates/{}".format(xml_file), params)
        self.set_scenario_xml(scenario)
        return self.go_to_assessment()

    def go_to_assessment(self):
        """ Navigates to assessment page """
        mentoring = self.go_to_view("student_view")

        class Namespace:
            pass

        controls = Namespace()

        controls.submit = mentoring.find_element_by_css_selector("input.input-main")
        controls.next_question = mentoring.find_element_by_css_selector("input.input-next")
        controls.review = mentoring.find_element_by_css_selector("input.input-review")
        controls.try_again = mentoring.find_element_by_css_selector("input.input-try-again")
        controls.review_link = mentoring.find_element_by_css_selector(".review-link a")

        return mentoring, controls

    def wait_for_init(self):
        """ Wait for the scenario to initialize """
        self.wait_until_visible(self.browser.find_elements_by_css_selector('.sb-step')[0])

    def assert_hidden(self, elem):
        self.assertFalse(elem.is_displayed())

    def assert_disabled(self, elem):
        self.assertTrue(elem.is_displayed())
        self.assertFalse(elem.is_enabled())

    def assert_clickable(self, elem):
        self.assertTrue(elem.is_displayed())
        self.assertTrue(elem.is_enabled())

    def ending_controls(self, controls, last):
        if last:
            self.assert_hidden(controls.next_question)
            self.assert_disabled(controls.review)
        else:
            self.assert_disabled(controls.next_question)
            self.assert_hidden(controls.review)

    def selected_controls(self, controls, last):
        self.assert_clickable(controls.submit)
        self.ending_controls(controls, last)

    def assert_message_text(self, mentoring, text):
        message_wrapper = mentoring.find_element_by_css_selector('.assessment-message')
        self.assertEqual(message_wrapper.text, text)
        self.assertTrue(message_wrapper.is_displayed())

    def assert_no_message_text(self, mentoring):
        message_wrapper = mentoring.find_element_by_css_selector('.assessment-message')
        self.assertEqual(message_wrapper.text, '')

    def check_question_feedback(self, step_builder, question):
        question_checkmark = step_builder.find_element_by_css_selector('.assessment-checkmark')
        question_feedback = question.find_element_by_css_selector(".feedback")
        self.assertTrue(question_feedback.is_displayed())
        self.assertEqual(question_feedback.text, "Question Feedback Message")

        question.click()
        self.assertFalse(question_feedback.is_displayed())

        question_checkmark.click()
        self.assertTrue(question_feedback.is_displayed())

    def do_submit_wait(self, controls, last):
        if last:
            self.wait_until_clickable(controls.review)
        else:
            self.wait_until_clickable(controls.next_question)

    def do_post(self, controls, last):
        if last:
            controls.review.click()
        else:
            controls.next_question.click()

    def multiple_response_question(self, number, mentoring, controls, choice_names, result, last=False):
        question = self.peek_at_multiple_response_question(number, mentoring, controls, last=last)

        choices = GetChoices(question)
        expected_choices = {
            "Its elegance": False,
            "Its beauty": False,
            "Its gracefulness": False,
            "Its bugs": False,
        }
        self.assertEquals(choices.state, expected_choices)

        for name in choice_names:
            choices.select(name)
            expected_choices[name] = True

        self.assertEquals(choices.state, expected_choices)

        self.selected_controls(controls, last)

        controls.submit.click()

        self.do_submit_wait(controls, last)
        self._assert_checkmark(mentoring, result)
        controls.review.click()

    def expect_question_visible(self, number, mentoring, question_text=None):
        if not question_text:
            question_text = self.question_text(number)
        self.wait_until_text_in(question_text, mentoring)
        question_div = None
        for xblock_div in mentoring.find_elements_by_css_selector('div.xblock-v1'):
            header_text = xblock_div.find_elements_by_css_selector('h4.question-title')
            if header_text and question_text in header_text[0].text:
                question_div = xblock_div
                self.assertTrue(xblock_div.is_displayed())
            elif header_text:
                self.assertFalse(xblock_div.is_displayed())
            # else this is an HTML block or something else, not a question step

        self.assertIsNotNone(question_div)
        return question_div

    def answer_mcq(self, number, name, value, mentoring, controls, is_last=False):
        self.expect_question_visible(number, mentoring)

        mentoring.find_element_by_css_selector('input[name={}][value={}]'.format(name, value)).click()
        controls.submit.click()
        if is_last:
            self.wait_until_clickable(controls.review)
            controls.review.click()
            self.wait_until_hidden(controls.review)
        else:
            self.wait_until_clickable(controls.next_question)
            controls.next_question.click()

    def _assert_checkmark(self, mentoring, result):
        """Assert that only the desired checkmark is present."""
        states = {CORRECT: 0, INCORRECT: 0, PARTIAL: 0}
        states[result] += 1

        for name, count in states.items():
            self.assertEqual(len(mentoring.find_elements_by_css_selector(".submit .checkmark-{}".format(name))), count)


class GetChoices:
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
