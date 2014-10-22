from .base_test import MentoringBaseTest

CORRECT, INCORRECT, PARTIAL = "correct", "incorrect", "partially-correct"

class MentoringAssessmentTest(MentoringBaseTest):
    def _selenium_bug_workaround_scroll_to(self, mentoring):
        """Workaround for selenium bug:

        Some version of Selenium has a bug that prevents scrolling
        to radiobuttons before being clicked. The click not taking
        place, when it's outside the view.

        Since the bug does not affect other content, asking Selenium
        to click on the legend first, will properly scroll it.

        It also have it's fair share of issues with the workbench header.

        For this reason we click on the bottom-most element, scrolling to it.
        Then, click on the title of the question (also scrolling to it)
        hopefully, this gives us enough room for the full step with the
        control buttons to fit.
        """
        controls = mentoring.find_element_by_css_selector("div.submit")
        title = mentoring.find_element_by_css_selector("h3.question-title")
        controls.click()
        title.click()

    def assert_hidden(self, elem):
        self.assertFalse(elem.is_displayed())

    def assert_disabled(self, elem):
        self.assertTrue(elem.is_displayed())
        self.assertFalse(elem.is_enabled())

    def assert_clickable(self, elem):
        self.assertTrue(elem.is_displayed())
        self.assertTrue(elem.is_enabled())

    def assert_persistent_elements_present(self, mentoring):
        self.assertIn("A Simple Assessment", mentoring.text)
        self.assertIn("This paragraph is shared between all questions.", mentoring.text)

    def assert_disabled(self, elem):
        self.assertTrue(elem.is_displayed())
        self.assertFalse(elem.is_enabled())

    class _GetChoices(object):
        def __init__(self, mentoring, selector=".choices"):
            self._mcq = mentoring.find_element_by_css_selector(selector)

        @property
        def text(self):
            return self._mcq.text

        @property
        def state(self):
            return {
                choice.text: choice.find_element_by_css_selector("input").is_selected()
                for choice in self._mcq.find_elements_by_css_selector(".choice")}

        def select(self, text):
            state = {}
            for choice in self._mcq.find_elements_by_css_selector(".choice"):
                if choice.text == text:
                    choice.find_element_by_css_selector("input").click()
                    return
            raise AssertionError("Expected selectable item present: {}".format(text))

    def _assert_checkmark(self, mentoring, result):
        """Assert that only the desired checkmark is present."""
        states = {CORRECT: 0, INCORRECT: 0, PARTIAL: 0}
        states[result] += 1

        for name, count in states.items():
            self.assertEqual(len(mentoring.find_elements_by_css_selector(".checkmark-{}".format(name))), count)


    def go_to_workbench_main_page(self):
        self.browser.get(self.live_server_url)

    def go_to_assessment_1(self):
        mentoring = self.go_to_page('Assessment 1')

        class Namespace(object):
            pass

        controls = Namespace()

        controls.submit = mentoring.find_element_by_css_selector("input.input-main")
        controls.next_question = mentoring.find_element_by_css_selector("input.input-next")
        controls.review = mentoring.find_element_by_css_selector("input.input-review")
        controls.try_again = mentoring.find_element_by_css_selector("input.input-try-again")

        return mentoring, controls

    def at_step_1_freeform_answer(self, mentoring, controls, text_input, result, saved_value=""):
        self.wait_until_text_in("QUESTION 1", mentoring)
        self.assert_persistent_elements_present(mentoring)
        self._selenium_bug_workaround_scroll_to(mentoring)

        answer = mentoring.find_element_by_css_selector("textarea.answer.editable")

        self.assertIn("Please answer the questions below.", mentoring.text)
        self.assertIn("QUESTION 1", mentoring.text)
        self.assertIn("What is your goal?", mentoring.text)

        self.assertEquals(saved_value, answer.get_attribute("value"))
        if not saved_value:
            self.assert_disabled(controls.submit)
        self.assert_disabled(controls.next_question)

        answer.clear()
        answer.send_keys(text_input)
        self.assertEquals(text_input, answer.get_attribute("value"))

        self.assert_clickable(controls.submit)
        self.assert_disabled(controls.next_question)
        self.assert_hidden(controls.review)
        self.assert_hidden(controls.try_again)

        controls.submit.click()

        self.wait_until_clickable(controls.next_question)
        self._assert_checkmark(mentoring, result)
        controls.next_question.click()

    def at_step_2_single_choice_question(self, mentoring, controls, choice_name, result):
        self.wait_until_text_in("QUESTION 2", mentoring)
        self.assert_persistent_elements_present(mentoring)
        self._selenium_bug_workaround_scroll_to(mentoring)
        self.assertIn("Do you like this MCQ?", mentoring.text)

        self.assert_disabled(controls.submit)
        self.assert_disabled(controls.next_question)
        self.assert_hidden(controls.review)
        self.assert_hidden(controls.try_again)

        choices = self._GetChoices(mentoring)
        expected_state = {"Yes": False, "Maybe not": False, "I don't understand": False}
        self.assertEquals(choices.state, expected_state)

        choices.select(choice_name)
        expected_state[choice_name] = True
        self.assertEquals(choices.state, expected_state)

        self.assert_clickable(controls.submit)
        self.assert_disabled(controls.next_question)
        self.assert_hidden(controls.review)
        self.assert_hidden(controls.try_again)

        controls.submit.click()

        self.wait_until_clickable(controls.next_question)
        self._assert_checkmark(mentoring, result)
        controls.next_question.click()

    def at_step_3_rating_question(self, mentoring, controls, choice_name, result):
        self.wait_until_text_in("QUESTION 3", mentoring)
        self.assert_persistent_elements_present(mentoring)
        self._selenium_bug_workaround_scroll_to(mentoring)
        self.assertIn("How much do you rate this MCQ?", mentoring.text)

        self.assert_disabled(controls.submit)
        self.assert_disabled(controls.next_question)
        self.assert_hidden(controls.review)
        self.assert_hidden(controls.try_again)

        choices = self._GetChoices(mentoring, ".rating")
        expected_choices = {
            "1 - Not good at all": False,
            "2": False, "3": False, "4": False,
            "5 - Extremely good": False,
            "I don't want to rate it": False,
        }
        self.assertEquals(choices.state, expected_choices)
        choices.select(choice_name)
        expected_choices[choice_name] = True
        self.assertEquals(choices.state, expected_choices)

        self.assert_clickable(controls.submit)
        self.assert_disabled(controls.next_question)
        self.assert_hidden(controls.review)
        self.assert_hidden(controls.try_again)

        controls.submit.click()

        self.wait_until_clickable(controls.next_question)
        self._assert_checkmark(mentoring, result)
        controls.next_question.click()

    def peek_at_step_4_multiple_choice_question(self, mentoring, controls):
        self.wait_until_text_in("QUESTION 4", mentoring)
        self.assert_persistent_elements_present(mentoring)
        self._selenium_bug_workaround_scroll_to(mentoring)
        self.assertIn("What do you like in this MRQ?", mentoring.text)

        self.assert_disabled(controls.submit)
        self.assert_hidden(controls.next_question)
        self.assert_disabled(controls.review)
        self.assert_hidden(controls.try_again)

    def at_step_4_multiple_choice_question(self, mentoring, controls, choice_names, result):
        self.peek_at_step_4_multiple_choice_question(mentoring, controls)

        choices = self._GetChoices(mentoring)
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

        self.assert_clickable(controls.submit)
        self.assert_hidden(controls.next_question)
        self.assert_disabled(controls.review)
        self.assert_hidden(controls.try_again)

        controls.submit.click()

        self.wait_until_clickable(controls.review)
        self._assert_checkmark(mentoring, result)
        controls.review.click()

    def peek_at_step_5_review(self, mentoring, controls, expected):
        self.wait_until_text_in("You scored {percentage}% on this assessment.".format(**expected), mentoring)
        self.assert_persistent_elements_present(mentoring)
        if expected["num_attempts"] < expected["max_attempts"]:
            self.assertIn("Note: if you retake this assessment, only your final score counts.", mentoring.text)
        self.assertIn("You answered {correct} questions correctly.".format(**expected), mentoring.text)
        self.assertIn("You answered {partial} questions partially correct.".format(**expected), mentoring.text)
        self.assertIn("You answered {incorrect} questions incorrectly.".format(**expected), mentoring.text)
        self.assertIn("You have used {num_attempts} of {max_attempts} submissions.".format(**expected), mentoring.text)

        self.assert_hidden(controls.submit)
        self.assert_hidden(controls.next_question)
        self.assert_hidden(controls.review)

    def test_assessment(self):
        mentoring, controls = self.go_to_assessment_1()

        self.at_step_1_freeform_answer(mentoring, controls, 'This is the answer', CORRECT)
        self.at_step_2_single_choice_question(mentoring, controls, 'Maybe not', INCORRECT)
        self.at_step_3_rating_question(mentoring, controls, "5 - Extremely good", CORRECT)
        self.peek_at_step_4_multiple_choice_question(mentoring, controls)

        # see if assessment remembers the current step
        self.go_to_workbench_main_page()
        mentoring, controls = self.go_to_assessment_1()

        self.at_step_4_multiple_choice_question(mentoring, controls, ("Its beauty",), PARTIAL)

        expected_results = {
                "correct": 2, "partial": 1, "incorrect": 1, "percentage": 63,
                "num_attempts": 1, "max_attempts": 2}
        self.peek_at_step_5_review(mentoring, controls, expected_results)

        self.assert_clickable(controls.try_again)
        controls.try_again.click()

        self.at_step_1_freeform_answer(mentoring, controls, 'This is a different answer', CORRECT,
                saved_value='This is the answer')
        self.at_step_2_single_choice_question(mentoring, controls, 'Yes', CORRECT)
        self.at_step_3_rating_question(mentoring, controls, "1 - Not good at all", INCORRECT)

        user_selection =  ("Its elegance", "Its beauty", "Its gracefulness")
        self.at_step_4_multiple_choice_question(mentoring, controls, user_selection, CORRECT)

        expected_results = {
                "correct": 3, "partial": 0, "incorrect": 1, "percentage": 75,
                "num_attempts": 2, "max_attempts": 2}
        self.peek_at_step_5_review(mentoring, controls, expected_results)
        self.assert_disabled(controls.try_again)
