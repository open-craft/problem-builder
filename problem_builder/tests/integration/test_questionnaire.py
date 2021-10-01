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

from .base_test import MentoringBaseTest

# Classes ###########################################################


@ddt.ddt
class QuestionnaireBlockTest(MentoringBaseTest):
    def _get_choice_label_text(self, choice):
        return choice.find_element_by_css_selector('label').text

    def _get_inputs(self, choices):
        return [choice.find_element_by_css_selector('input') for choice in choices]

    def assert_messages_empty(self, messages):
        self.assertEqual(messages.text, '')
        self.assertFalse(messages.find_elements_by_xpath('./*'))

    def _click_result_icon(self, choice):
        choice.find_element_by_css_selector(".choice-result").click()

    def test_mcq_choices_rating(self):
        """
        Mentoring MCQ should display tips according to user choice
        """
        # Initial MCQ status
        mentoring = self.go_to_page('Mcq 1')
        mcq1 = mentoring.find_element_by_css_selector('fieldset.choices')
        mcq1_heading = mentoring.find_element_by_id('heading_' + mcq1.get_attribute('id'))
        mcq2 = mentoring.find_element_by_css_selector('fieldset.rating')
        mcq2_heading = mentoring.find_element_by_id('heading_' + mcq2.get_attribute('id'))
        messages = mentoring.find_element_by_css_selector('.messages')
        submit = mentoring.find_element_by_css_selector('.submit input.input-main')

        self.assert_messages_empty(messages)
        self.assertFalse(submit.is_enabled())

        self.assertEqual(mcq1_heading.text, 'Question 1')
        self.assertEqual(mcq1.find_element_by_css_selector('legend').text, 'Do you like this MCQ?')
        self.assertEqual(mcq2_heading.text, 'Question 2')
        self.assertEqual(mcq2.find_element_by_css_selector('legend').text, 'How do you rate this MCQ?')

        mcq1_choices = mcq1.find_elements_by_css_selector('.choices .choice')
        mcq2_choices = mcq2.find_elements_by_css_selector('.rating .choice')

        mcq1_choices_input = self._get_inputs(mcq1_choices)
        mcq2_choices_input = self._get_inputs(mcq2_choices)

        self.assertListEqual(
            [self._get_choice_label_text(choice) for choice in mcq1_choices],
            ["Yes", "Maybe not", "I don't understand"]
        )
        self.assertListEqual(
            [self._get_choice_label_text(choice) for choice in mcq2_choices],
            ['1 - Not good at all', '2', '3', '4', '5 - Extremely good', "I don't want to rate it"]
        )

        self.assertListEqual(
            [choice_input.get_attribute('value') for choice_input in mcq1_choices_input],
            ['yes', 'maybenot', 'understand']
        )

        self.assertListEqual(
            [choice_input.get_attribute('value') for choice_input in mcq2_choices_input],
            ['1', '2', '3', '4', '5', 'notwant']
        )

        def submit_answer_and_assert_messages(
                mcq1_answer, mcq2_answer, item_feedback1, item_feedback2,
                feedback1_selector=".choice-tips .tip p",
                feedback2_selector=".choice-tips .tip p"):

            mcq1_choices_input[mcq1_answer].click()
            mcq2_choices_input[mcq2_answer].click()
            self.assertTrue(submit.is_enabled())
            submit.click()
            self.wait_until_disabled(submit)

            mcq1_feedback = mcq1.find_element_by_css_selector(feedback1_selector)
            mcq2_feedback = mcq2.find_element_by_css_selector(feedback2_selector)

            self.assertEqual(mcq1_feedback.text, item_feedback1)
            self.assertTrue(mcq1_feedback.is_displayed())

            self.assertEqual(mcq2_feedback.text, item_feedback2)
            self.assertTrue(mcq2_feedback.is_displayed())

        # Submit button disabled without selecting anything
        self.assertFalse(submit.is_enabled())

        # Submit button stays disabled when there are unfinished mcqs
        mcq1_choices_input[1].click()
        self.assertFalse(submit.is_enabled())

        # Should not show full completion message when wrong answers are selected
        submit_answer_and_assert_messages(0, 2, 'Great!', 'Will do better next time...')
        self.assertEqual(messages.text, '')
        self.assertFalse(messages.is_displayed())

        # When selected answers have no tips display generic feedback message
        submit_answer_and_assert_messages(
            1, 5, 'Feedback message 1', 'Feedback message 2',
            ".feedback .message-content", ".feedback .message-content"
        )
        self.assertEqual(messages.text, '')
        self.assertFalse(messages.is_displayed())

        # Should show full completion when the right answers are selected
        submit_answer_and_assert_messages(0, 3, 'Great!', 'I love good grades.')
        self.assertIn('All is good now...\nCongratulations!', messages.text)
        self.assertTrue(messages.is_displayed())

        # The choice tip containers should have the with-tips class.
        mcq1_tip_containers = mcq1.find_elements_by_css_selector('.choice-tips-container.with-tips')
        mcq2_tip_containers = mcq2.find_elements_by_css_selector('.choice-tips-container.with-tips')
        self.assertEqual(len(mcq1_tip_containers), 3)
        self.assertEqual(len(mcq2_tip_containers), 6)

        # Clicking outside the tips should hide the tips and clear the with-tips class.
        mcq1_tips = mcq1.find_element_by_css_selector(".choice-tips .tip p")
        mcq2_tips = mcq2.find_element_by_css_selector(".choice-tips .tip p")
        mcq1_heading.click()
        mcq2_heading.click()
        mcq1_tip_containers = mcq1.find_elements_by_css_selector('.choice-tips-container.with-tips')
        mcq2_tip_containers = mcq2.find_elements_by_css_selector('.choice-tips-container.with-tips')
        self.assertEqual(len(mcq1_tip_containers), 0)
        self.assertEqual(len(mcq2_tip_containers), 0)
        self.assertFalse(mcq1_tips.is_displayed())
        self.assertFalse(mcq2_tips.is_displayed())

    def test_mrq_with_comments(self):
        mentoring = self.go_to_page('Mrq With Comments 1')
        mcq = mentoring.find_element_by_css_selector('fieldset.choices')
        messages = mentoring.find_element_by_css_selector('.messages')
        submit = mentoring.find_element_by_css_selector('.submit input.input-main')

        self.assertEqual(messages.text, '')
        self.assertFalse(messages.find_elements_by_xpath('./*'))
        self.assertFalse(submit.is_enabled())

        mcq_legend = mcq.find_element_by_css_selector('legend')
        self.assertEqual(mcq_legend.text, 'What do you like in this MRQ?')

        mcq_heading = mentoring.find_element_by_id('heading_' + mcq.get_attribute('id'))
        self.assertEqual(mcq_heading.text, 'Question')

        mcq_choices = mcq.find_elements_by_css_selector('.choices .choice')

        self.assertEqual(len(mcq_choices), 4)
        self.assertListEqual(
            [self._get_choice_label_text(choice) for choice in mcq_choices],
            ['Its elegance', 'Its beauty', "Its gracefulness", "Its bugs"]
        )

        mcq_choices_input = self._get_inputs(mcq_choices)
        self.assertEqual(mcq_choices_input[0].get_attribute('value'), 'elegance')
        self.assertEqual(mcq_choices_input[1].get_attribute('value'), 'beauty')
        self.assertEqual(mcq_choices_input[2].get_attribute('value'), 'gracefulness')
        self.assertEqual(mcq_choices_input[3].get_attribute('value'), 'bugs')

    def test_mrq_feedback_popups(self):
        mentoring = self.go_to_page('Mrq With Comments 1')

        item_feedbacks = [
            "This is something everyone has to like about this MRQ",
            "This is something everyone has to like about beauty",
            "This MRQ is indeed very graceful",
            "Nah, there aren\\'t any!"
        ]
        self.popup_check(mentoring, item_feedbacks, prefix='div[data-name="mrq_1_1_7"]')

        for index, _ in enumerate(item_feedbacks):
            choice_wrapper = mentoring.find_elements_by_css_selector('div[data-name="mrq_1_1_7"]' + " .choice")[index]
            choice_wrapper.find_element_by_css_selector(".choice-selector input").click()
            item_feedback_icon = choice_wrapper.find_element_by_css_selector(".choice-result")
            if item_feedback_icon.is_displayed():
                item_feedback_icon.click()  # clicking on item feedback icon
            item_feedback_popup = choice_wrapper.find_element_by_css_selector(".choice-tips")

            self.assertFalse(item_feedback_popup.is_displayed())
            self.assertEqual(item_feedback_popup.text, "")

    def _get_questionnaire_options(self, questionnaire):
        result = []
        # this could be a list comprehension, but a bit complicated one - hence explicit loop
        for choice_wrapper in questionnaire.find_elements_by_css_selector(".choice"):
            choice_label = choice_wrapper.find_element_by_css_selector("label")
            result.append(choice_label)
        return result

    @ddt.data(
        'Mrq With Html Choices',
        'Mcq With Html Choices'
    )
    def test_questionnaire_html_choices(self, page):

        mentoring = self.go_to_page(page)

        question = mentoring.find_element_by_css_selector('fieldset legend')
        self.assertIn(
            'What do <strong>you</strong> like in this ',
            question.get_attribute('innerHTML').strip()
        )

        choices_list = mentoring.find_element_by_css_selector(".choices-list")
        messages = mentoring.find_element_by_css_selector('.messages')

        expected_options = [
            "<strong>Its elegance</strong>",
            "<em>Its beauty</em>",
            "<strong>Its gracefulness</strong>",
            '<span style="font-color:red">Its bugs</span>'
        ]

        # Ensure each questionnaire label contains the input item, and the expected option.
        labels = self._get_questionnaire_options(choices_list)
        self.assertEqual(len(labels), len(expected_options))
        for idx, label in enumerate(labels):
            self.assertEqual(len(label.find_elements_by_tag_name('input')), 1)
            self.assertIn(expected_options[idx], label.get_attribute('innerHTML').strip())

        self.assert_messages_empty(messages)

        submit = mentoring.find_element_by_css_selector('.submit input.input-main')
        self.assertFalse(submit.is_enabled())

        inputs = choices_list.find_elements_by_css_selector('.choice-selector input')
        inputs[0].click()
        inputs[1].click()
        inputs[2].click()

        self.assertTrue(submit.is_enabled())
        submit.click()
        self.wait_until_disabled(submit)

        self.assertIn('Congratulations!', messages.text)

    def _get_inner_height(self, elem):
        return elem.size['height'] - \
            int(elem.value_of_css_property("padding-top").replace('px', '')) - \
            int(elem.value_of_css_property("padding-bottom").replace('px', ''))

    @ddt.unpack
    @ddt.data(
        ('yes', 33),
        ('maybenot', 60),
        ('understand', 600)
    )
    def test_tip_height(self, choice_value, expected_height):
        mentoring = self.go_to_page("Mcq With Fixed Height Tips")
        choices_list = mentoring.find_element_by_css_selector(".choices-list")
        submit = mentoring.find_element_by_css_selector('.submit input.input-main')

        choice_input_css_selector = f".choice input[value={choice_value}]"
        choice_input = choices_list.find_element_by_css_selector(choice_input_css_selector)
        choice_wrapper = choice_input.find_element_by_xpath("./ancestor::div[@class='choice']")

        choice_input.click()
        self.wait_until_clickable(submit)
        submit.click()
        self.wait_until_disabled(submit)

        self._click_result_icon(choice_wrapper)
        item_feedback_popup = choice_wrapper.find_element_by_css_selector(".choice-tips")
        self.assertTrue(item_feedback_popup.is_displayed())
        feedback_height = self._get_inner_height(item_feedback_popup)
        self.assertEqual(feedback_height, expected_height)


class QuestionnaireBlockAprosThemeTest(QuestionnaireBlockTest):
    """
    Test MRQ/MCQ questions without the LMS theme which is on by default.
    """
    pass
