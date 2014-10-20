from .base_test import MentoringBaseTest


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

    def test_assessment(self):
        # step 1 -- freeform answer
        mentoring = self.go_to_page('Assessment 1')
        self.assert_persistent_elements_present(mentoring)
        self._selenium_bug_workaround_scroll_to(mentoring)

        submit = mentoring.find_element_by_css_selector("input.input-main")
        next_question = mentoring.find_element_by_css_selector("input.input-next")
        review = mentoring.find_element_by_css_selector("input.input-review")
        try_again = mentoring.find_element_by_css_selector("input.input-try-again")

        answer = mentoring.find_element_by_css_selector("textarea.answer.editable")

        self.assertIn("Please answer the questions below.", mentoring.text)
        self.assertIn("QUESTION 1", mentoring.text)
        self.assertIn("What is your goal?", mentoring.text)

        self.assertEquals("", answer.get_attribute("value"))
        self.assert_disabled(submit)
        self.assert_disabled(next_question)

        answer.send_keys('This is the answer')
        self.assertEquals('This is the answer', answer.get_attribute("value"))

        self.assert_clickable(submit)
        self.assert_disabled(next_question)
        self.assert_hidden(review)
        self.assert_hidden(try_again)

        submit.click()

        self.wait_until_clickable(next_question)
        next_question.click()

        # step 2 -- single choice question
        self.wait_until_text_in("QUESTION 2", mentoring)
        self.assert_persistent_elements_present(mentoring)
        self._selenium_bug_workaround_scroll_to(mentoring)
        self.assertIn("Do you like this MCQ?", mentoring.text)

        self.assert_disabled(submit)
        self.assert_disabled(next_question)
        self.assert_hidden(review)
        self.assert_hidden(try_again)

        choices = self._GetChoices(mentoring)
        self.assertEquals(choices.state, {"Yes": False, "Maybe not": False, "I don't understand": False})

        choices.select("Yes")
        self.assertEquals(choices.state, {"Yes": True, "Maybe not": False, "I don't understand": False})
        self.assert_clickable(submit)
        self.assert_disabled(next_question)
        self.assert_hidden(review)
        self.assert_hidden(try_again)

        submit.click()

        self.wait_until_clickable(next_question)
        next_question.click()

        # step 3 -- rating question
        self.wait_until_text_in("QUESTION 3", mentoring)
        self.assert_persistent_elements_present(mentoring)
        self._selenium_bug_workaround_scroll_to(mentoring)
        self.assertIn("How much do you rate this MCQ?", mentoring.text)

        self.assert_disabled(submit)
        self.assert_disabled(next_question)
        self.assert_hidden(review)
        self.assert_hidden(try_again)

        choices = self._GetChoices(mentoring, ".rating")
        self.assertEquals(choices.state, {
            "1 - Not good at all": False,
            "2": False, "3": False, "4": False,
            "5 - Extremely good": False,
            "I don't want to rate it": False,
        })
        choices.select("5 - Extremely good")
        self.assertEquals(choices.state, {
            "1 - Not good at all": False,
            "2": False, "3": False, "4": False,
            "5 - Extremely good": True,
            "I don't want to rate it": False,
        })

        self.assert_clickable(submit)
        self.assert_disabled(next_question)
        self.assert_hidden(review)
        self.assert_hidden(try_again)

        submit.click()

        self.wait_until_clickable(next_question)
        next_question.click()

        # step 4 -- multiple choice question
        self.wait_until_text_in("QUESTION 4", mentoring)
        self.assert_persistent_elements_present(mentoring)
        self._selenium_bug_workaround_scroll_to(mentoring)
        self.assertIn("What do you like in this MRQ?", mentoring.text)

        self.assert_disabled(submit)
        self.assert_hidden(next_question)
        self.assert_disabled(review)
        self.assert_hidden(try_again)

        # see if assessment remembers the current step
        self.browser.get(self.live_server_url)
        # step 4 -- a second time
        mentoring = self.go_to_page("Assessment 1")

        self.wait_until_text_in("QUESTION 4", mentoring)
        self.assert_persistent_elements_present(mentoring)
        self._selenium_bug_workaround_scroll_to(mentoring)
        self.assertIn("What do you like in this MRQ?", mentoring.text)

        submit = mentoring.find_element_by_css_selector("input.input-main")
        next_question = mentoring.find_element_by_css_selector("input.input-next")
        review = mentoring.find_element_by_css_selector("input.input-review")
        try_again = mentoring.find_element_by_css_selector("input.input-try-again")

        self.assert_disabled(submit)
        self.assert_hidden(next_question)
        self.assert_disabled(review)
        self.assert_hidden(try_again)

        choices = self._GetChoices(mentoring)
        self.assertEquals(choices.state, {
            "Its elegance": False,
            "Its beauty": False,
            "Its gracefulness": False,
            "Its bugs": False,
        })
        choices.select("Its elegance")
        choices.select("Its beauty")
        choices.select("Its gracefulness")
        self.assertEquals(choices.state, {
            "Its elegance": True,
            "Its beauty": True,
            "Its gracefulness": True,
            "Its bugs": False,
        })

        self.assert_clickable(submit)
        self.assert_hidden(next_question)
        self.assert_disabled(review)
        self.assert_hidden(try_again)

        submit.click()

        self.wait_until_clickable(review)
        review.click()

        # step 5 -- review
        self.wait_until_text_in("You scored 100% on this assessment.", mentoring)
        self.assert_persistent_elements_present(mentoring)
        self.assertIn("Note: if you retake this assessment, only your final score counts.", mentoring.text)
        self.assertIn("You answered 4 questions correctly.", mentoring.text)
        self.assertIn("You answered 0 questions partially correct.", mentoring.text)
        self.assertIn("You answered 0 questions incorrectly.", mentoring.text)

        self.assert_hidden(submit)
        self.assert_hidden(next_question)
        self.assert_hidden(review)
        self.assert_disabled(try_again)
