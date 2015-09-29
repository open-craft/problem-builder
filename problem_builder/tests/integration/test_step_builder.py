from .base_test import CORRECT, INCORRECT, PARTIAL, MentoringAssessmentBaseTest, GetChoices

from ddt import ddt, data


@ddt
class StepBuilderTest(MentoringAssessmentBaseTest):

    def freeform_answer(self, number, step_builder, controls, text_input, result, saved_value="", last=False):
        self.expect_question_visible(number, step_builder)

        answer = step_builder.find_element_by_css_selector("textarea.answer.editable")

        self.assertIn(self.question_text(number), step_builder.text)
        self.assertIn("What is your goal?", step_builder.text)

        self.assertEquals(saved_value, answer.get_attribute("value"))
        if not saved_value:
            self.assert_disabled(controls.submit)
        self.assert_disabled(controls.next_question)

        answer.clear()
        answer.send_keys(text_input)
        self.assertEquals(text_input, answer.get_attribute("value"))

        self.assert_clickable(controls.submit)
        self.ending_controls(controls, last)
        self.assert_hidden(controls.review)
        self.assert_hidden(controls.try_again)

        controls.submit.click()

        self.do_submit_wait(controls, last)
        self._assert_checkmark(step_builder, result)
        self.do_post(controls, last)

    def single_choice_question(self, number, step_builder, controls, choice_name, result, last=False):
        question = self.expect_question_visible(number, step_builder)

        self.assertIn("Do you like this MCQ?", question.text)

        self.assert_disabled(controls.submit)
        self.ending_controls(controls, last)
        self.assert_hidden(controls.try_again)

        choices = GetChoices(question)
        expected_state = {"Yes": False, "Maybe not": False, "I don't understand": False}
        self.assertEquals(choices.state, expected_state)

        choices.select(choice_name)
        expected_state[choice_name] = True
        self.assertEquals(choices.state, expected_state)

        self.selected_controls(controls, last)

        controls.submit.click()

        self.do_submit_wait(controls, last)
        self._assert_checkmark(step_builder, result)

        self.do_post(controls, last)

    def rating_question(self, number, step_builder, controls, choice_name, result, last=False):
        self.expect_question_visible(number, step_builder)

        self.assertIn("How much do you rate this MCQ?", step_builder.text)

        self.assert_disabled(controls.submit)
        self.ending_controls(controls, last)
        self.assert_hidden(controls.try_again)

        choices = GetChoices(step_builder, ".rating")
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

        self.ending_controls(controls, last)

        controls.submit.click()

        self.do_submit_wait(controls, last)
        self._assert_checkmark(step_builder, result)
        self.do_post(controls, last)

    def peek_at_multiple_response_question(
        self, number, step_builder, controls, last=False, extended_feedback=False, alternative_review=False
    ):
        question = self.expect_question_visible(number, step_builder)
        self.assertIn("What do you like in this MRQ?", step_builder.text)
        return question

        if extended_feedback:
            self.assert_disabled(controls.submit)
            self.check_question_feedback(step_builder, question)
            if alternative_review:
                self.assert_clickable(controls.review_link)
                self.assert_hidden(controls.try_again)

    def peek_at_review(self, step_builder, controls, expected, extended_feedback=False):
        self.wait_until_text_in("You scored {percentage}% on this assessment.".format(**expected), step_builder)

        # Check grade breakdown
        if expected["correct"] == 1:
            self.assertIn("You answered 1 questions correctly.".format(**expected), step_builder.text)
        else:
            self.assertIn("You answered {correct} questions correctly.".format(**expected), step_builder.text)

        if expected["partial"] == 1:
            self.assertIn("You answered 1 question partially correctly.", step_builder.text)
        else:
            self.assertIn("You answered {partial} questions partially correctly.".format(**expected), step_builder.text)

        if expected["incorrect"] == 1:
            self.assertIn("You answered 1 question incorrectly.", step_builder.text)
        else:
            self.assertIn("You answered {incorrect} questions incorrectly.".format(**expected), step_builder.text)

        # Check presence of review links
        # - If unlimited attempts: no review links
        # - If limited attempts:
        #   - If not max attempts reached: no review links
        #   - If max attempts reached:
        #     - If extended feedback: review links available
        #     - If not extended feedback: review links

        review_list = step_builder.find_elements_by_css_selector('.review-list')

        if expected["max_attempts"] == 0:
            self.assertFalse(review_list)
        else:
            if expected["num_attempts"] < expected["max_attempts"]:
                self.assertFalse(review_list)
            elif expected["num_attempts"] == expected["max_attempts"]:
                if extended_feedback:
                    for correctness in ['correct', 'incorrect', 'partial']:
                        review_items = step_builder.find_elements_by_css_selector('.%s-list li' % correctness)
                        self.assertEqual(len(review_items), expected[correctness])
                else:
                    self.assertFalse(review_list)

        # Check if info about number of attempts used is correct
        if expected["max_attempts"] == 1:
            self.assertIn("You have used {num_attempts} of 1 submission.".format(**expected), step_builder.text)
        elif expected["max_attempts"] == 0:
            self.assertNotIn("You have used", step_builder.text)
        else:
            self.assertIn(
                "You have used {num_attempts} of {max_attempts} submissions.".format(**expected),
                step_builder.text
            )

        # Check controls
        self.assert_hidden(controls.submit)
        self.assert_hidden(controls.next_question)
        self.assert_hidden(controls.review)
        self.assert_hidden(controls.review_link)

    def popup_check(self, step_builder, item_feedbacks, prefix='', do_submit=True):
        for index, expected_feedback in enumerate(item_feedbacks):
            choice_wrapper = step_builder.find_elements_by_css_selector(prefix + " .choice")[index]
            choice_wrapper.click()

            item_feedback_icon = choice_wrapper.find_element_by_css_selector(".choice-result")
            item_feedback_icon.click()

            item_feedback_popup = choice_wrapper.find_element_by_css_selector(".choice-tips")
            self.assertTrue(item_feedback_popup.is_displayed())
            self.assertEqual(item_feedback_popup.text, expected_feedback)

            item_feedback_popup.click()
            self.assertTrue(item_feedback_popup.is_displayed())

            step_builder.click()
            self.assertFalse(item_feedback_popup.is_displayed())

    def extended_feedback_checks(self, step_builder, controls, expected_results):
        # MRQ is third correctly answered question
        self.assert_hidden(controls.review_link)
        step_builder.find_elements_by_css_selector('.correct-list li a')[2].click()
        self.peek_at_multiple_response_question(
            None, step_builder, controls, extended_feedback=True, alternative_review=True
        )

        # Step should display 5 checkmarks (4 correct items for MRQ, plus step-level feedback about correctness)
        correct_marks = step_builder.find_elements_by_css_selector('.checkmark-correct')
        incorrect_marks = step_builder.find_elements_by_css_selector('.checkmark-incorrect')
        self.assertEqual(len(correct_marks), 5)
        self.assertEqual(len(incorrect_marks), 0)

        item_feedbacks = [
            "This is something everyone has to like about this MRQ",
            "This is something everyone has to like about this MRQ",
            "This MRQ is indeed very graceful",
            "Nah, there aren't any!"
        ]
        self.popup_check(step_builder, item_feedbacks, prefix='div[data-name="mrq_1_1"]', do_submit=False)
        controls.review_link.click()
        self.peek_at_review(step_builder, controls, expected_results, extended_feedback=True)

        # Review rating question (directly precedes MRQ)
        step_builder.find_elements_by_css_selector('.incorrect-list li a')[0].click()
        # It should be possible to visit the MRQ from here
        self.wait_until_clickable(controls.next_question)
        controls.next_question.click()
        self.peek_at_multiple_response_question(
            None, step_builder, controls, extended_feedback=True, alternative_review=True
        )

    @data(
        {"max_attempts": 0, "extended_feedback": False},  # Unlimited attempts, no extended feedback
        {"max_attempts": 1, "extended_feedback": True},  # Limited attempts, extended feedback
        {"max_attempts": 1, "extended_feedback": False},  # Limited attempts, no extended feedback
        {"max_attempts": 2, "extended_feedback": True},  # Limited attempts, extended feedback
    )
    def test_step_builder(self, params):
        max_attempts = params['max_attempts']
        extended_feedback = params['extended_feedback']
        step_builder, controls = self.load_assessment_scenario("step_builder.xml", params)

        # Step 1
        # Submit free-form answer, go to next step
        self.freeform_answer(None, step_builder, controls, 'This is the answer', CORRECT)

        # Step 2
        # Submit MCQ, go to next step
        self.single_choice_question(None, step_builder, controls, 'Maybe not', INCORRECT)

        # Step 3
        # Submit rating, go to next step
        self.rating_question(None, step_builder, controls, "5 - Extremely good", CORRECT)

        # Last step
        # Submit MRQ, go to review
        self.multiple_response_question(None, step_builder, controls, ("Its beauty",), PARTIAL, last=True)

        # Review step
        expected_results = {
            "correct": 2, "partial": 1, "incorrect": 1, "percentage": 63,
            "num_attempts": 1, "max_attempts": max_attempts
        }
        self.peek_at_review(step_builder, controls, expected_results, extended_feedback=extended_feedback)

        if max_attempts == 1:
            self.assert_message_text(step_builder, "On review message text")
            self.assert_disabled(controls.try_again)
            return

        self.assert_message_text(step_builder, "Block incomplete message text")
        self.assert_clickable(controls.try_again)

        # Try again
        controls.try_again.click()

        self.wait_until_hidden(controls.try_again)
        self.assert_no_message_text(step_builder)

        self.freeform_answer(
            None, step_builder, controls, 'This is a different answer', CORRECT, saved_value='This is the answer'
        )
        self.single_choice_question(None, step_builder, controls, 'Yes', CORRECT)
        self.rating_question(None, step_builder, controls, "1 - Not good at all", INCORRECT)

        user_selection = ("Its elegance", "Its beauty", "Its gracefulness")
        self.multiple_response_question(None, step_builder, controls, user_selection, CORRECT, last=True)

        expected_results = {
            "correct": 3, "partial": 0, "incorrect": 1, "percentage": 75,
            "num_attempts": 2, "max_attempts": max_attempts
        }
        self.peek_at_review(step_builder, controls, expected_results, extended_feedback=extended_feedback)

        if max_attempts == 2:
            self.assert_disabled(controls.try_again)
        else:
            self.assert_clickable(controls.try_again)

        if 1 <= max_attempts <= 2:
            self.assert_message_text(step_builder, "On review message text")
        else:
            self.assert_message_text(step_builder, "Block incomplete message text")

        if extended_feedback:
            self.extended_feedback_checks(step_builder, controls, expected_results)

    def test_review_tips(self):
        params = {
            "max_attempts": 3,
            "extended_feedback": False,
            "include_review_tips": True
        }
        step_builder, controls = self.load_assessment_scenario("step_builder.xml", params)

        # Get one question wrong and one partially wrong on attempt 1 of 3: ####################
        self.freeform_answer(None, step_builder, controls, 'This is the answer', CORRECT)
        self.single_choice_question(None, step_builder, controls, 'Maybe not', INCORRECT)
        self.rating_question(None, step_builder, controls, "5 - Extremely good", CORRECT)
        self.multiple_response_question(None, step_builder, controls, ("Its beauty",), PARTIAL, last=True)

        # The review tips for MCQ 2 and the MRQ should be shown:
        review_tips = step_builder.find_element_by_css_selector('.assessment-review-tips')
        self.assertTrue(review_tips.is_displayed())
        self.assertIn('You might consider reviewing the following items', review_tips.text)
        self.assertIn('Take another look at', review_tips.text)
        self.assertIn('Lesson 1', review_tips.text)
        self.assertNotIn('Lesson 2', review_tips.text)  # This MCQ was correct
        self.assertIn('Lesson 3', review_tips.text)
        # If attempts remain and student got some answers wrong, show "incomplete" message
        self.assert_message_text(step_builder, "Block incomplete message text")

        # Try again
        self.assert_clickable(controls.try_again)
        controls.try_again.click()

        # Get no questions wrong on attempt 2 of 3: ############################################
        self.freeform_answer(
            None, step_builder, controls, 'This is the answer', CORRECT, saved_value='This is the answer'
        )
        self.single_choice_question(None, step_builder, controls, 'Yes', CORRECT)
        self.rating_question(None, step_builder, controls, "5 - Extremely good", CORRECT)
        user_selection = ("Its elegance", "Its beauty", "Its gracefulness")
        self.multiple_response_question(None, step_builder, controls, user_selection, CORRECT, last=True)

        # If attempts remain and student got all answers right, show "complete" message
        self.assert_message_text(step_builder, "Block completed message text")
        self.assertFalse(review_tips.is_displayed())

        # Try again
        self.assert_clickable(controls.try_again)
        controls.try_again.click()

        # Get some questions wrong again on attempt 3 of 3:
        self.freeform_answer(
            None, step_builder, controls, 'This is the answer', CORRECT, saved_value='This is the answer'
        )
        self.single_choice_question(None, step_builder, controls, 'Maybe not', INCORRECT)
        self.rating_question(None, step_builder, controls, "1 - Not good at all", INCORRECT)
        self.multiple_response_question(None, step_builder, controls, ("Its beauty",), PARTIAL, last=True)

        # The review tips will not be shown because no attempts remain:
        self.assertFalse(review_tips.is_displayed())
