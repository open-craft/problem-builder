from mock import patch
from ddt import ddt, data

from workbench.runtime import WorkbenchRuntime
from .base_test import CORRECT, INCORRECT, PARTIAL, MentoringAssessmentBaseTest, GetChoices
from .test_dashboard import MockSubmissionsAPI


class ExtendedMockSubmissionsAPI(MockSubmissionsAPI):
    def get_all_submissions(self, course_key_str, block_id, block_type):
        return (
            submission for submission in self.submissions.values() if
            submission['student_item']['item_id'] == block_id
        )


@ddt
class StepBuilderTest(MentoringAssessmentBaseTest):

    def setUp(self):
        super(StepBuilderTest, self).setUp()

        mock_submissions_api = ExtendedMockSubmissionsAPI()
        patches = (
            (
                "problem_builder.plot.PlotBlock.course_key_str",
                property(lambda block: "course_id")
            ),
            (
                "problem_builder.plot.sub_api",
                mock_submissions_api
            ),
            (
                "problem_builder.mcq.sub_api",
                mock_submissions_api
            ),
            (
                "problem_builder.sub_api.SubmittingXBlockMixin.student_item_key",
                property(
                    lambda block: dict(
                        student_id="student_id",
                        course_id="course_id",
                        item_id=block.scope_ids.usage_id,
                        item_type="pb-rating"
                    )
                )
            ),
        )
        for p in patches:
            patcher = patch(*p)
            patcher.start()
            self.addCleanup(patcher.stop)

        runtime_patcher = patch(
            'workbench.runtime.WorkbenchRuntime.anonymous_student_id',
            property(lambda runtime: "student_id"),
            create=True
        )
        runtime_patcher.start()
        self.addCleanup(runtime_patcher.stop)

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
            self.assertIn("You answered 1 question correctly.".format(**expected), step_builder.text)
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
        self.html_section(step_builder, controls)
        self.peek_at_multiple_response_question(
            None, step_builder, controls, extended_feedback=True, alternative_review=True
        )

    def test_next_label(self):
        step_builder, controls = self.load_assessment_scenario("step_builder_next.xml")
        self.expect_question_visible(None, step_builder)
        self.assertEqual(controls.next_question.get_attribute('value'), "Next Challenge")
        self.freeform_answer(None, step_builder, controls, 'This is the answer', CORRECT)
        self.expect_question_visible(None, step_builder)
        self.assertEqual(controls.next_question.get_attribute('value'), "Next Item")
        self.single_choice_question(None, step_builder, controls, 'Maybe not', INCORRECT)
        self.rating_question(None, step_builder, controls, "5 - Extremely good", CORRECT, last=True)

        # Check extended feedback loads the labels correctly.
        step_builder.find_elements_by_css_selector('.correct-list li a')[0].click()
        self.expect_question_visible(None, step_builder)
        self.assertEqual(controls.next_question.get_attribute('value'), "Next Challenge")

    def html_section(self, step_builder, controls, last=False):
        self.wait_until_hidden(controls.submit)
        target_control = controls.review if last else controls.next_question
        self.wait_until_clickable(target_control)
        target_control.click()

    def test_html_last(self):
        step_builder, controls = self.load_assessment_scenario("step_builder_html_last.xml")
        # Step 1
        # Submit free-form answer, go to next step
        self.freeform_answer(None, step_builder, controls, 'This is the answer', CORRECT)

        # Step 2
        # Submit MCQ, go to next step
        self.single_choice_question(None, step_builder, controls, 'Maybe not', INCORRECT)

        self.html_section(step_builder, controls, last=True)

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

        # Step 4, html with no question.
        self.html_section(step_builder, controls)

        # Last step
        # Submit MRQ, go to review
        with patch.object(WorkbenchRuntime, 'publish') as patched_method:
            self.multiple_response_question(None, step_builder, controls, ("Its beauty",), PARTIAL, last=True)

            # Check if "grade" event was published
            # Note that we can't use patched_method.assert_called_once_with here
            # because there is no way to obtain a reference to the block instance generated from the XML scenario
            self.assertTrue(patched_method.called)
            self.assertEquals(len(patched_method.call_args_list), 1)

            block_object = self.load_root_xblock()

            positional_args = patched_method.call_args[0]
            block, event, data = positional_args

            self.assertEquals(block.scope_ids.usage_id, block_object.scope_ids.usage_id)
            self.assertEquals(event, 'grade')
            self.assertEquals(data, {'value': 0.625, 'max_value': 1})

        # Review step
        expected_results = {
            "correct": 2, "partial": 1, "incorrect": 1, "percentage": 63,
            "num_attempts": 1, "max_attempts": max_attempts
        }
        self.peek_at_review(step_builder, controls, expected_results, extended_feedback=extended_feedback)
        if extended_feedback and max_attempts == 1:
            self.assertIn("Question 1 and Question 3", step_builder.find_element_by_css_selector('.correct-list').text)

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

        # Step 1
        # Submit free-form answer, go to next step
        self.freeform_answer(
            None, step_builder, controls, 'This is a different answer', CORRECT, saved_value='This is the answer'
        )
        # Step 2
        # Submit MCQ, go to next step
        self.single_choice_question(None, step_builder, controls, 'Yes', CORRECT)
        # Step 3
        # Submit rating, go to next step
        self.rating_question(None, step_builder, controls, "1 - Not good at all", INCORRECT)

        # Step 4, read only. Go to next step.
        self.html_section(step_builder, controls)
        # Last step
        # Submit MRQ, go to review
        user_selection = ("Its elegance", "Its beauty", "Its gracefulness")
        self.multiple_response_question(None, step_builder, controls, user_selection, CORRECT, last=True)

        # Review step
        expected_results = {
            "correct": 3, "partial": 0, "incorrect": 1, "percentage": 75,
            "num_attempts": 2, "max_attempts": max_attempts
        }
        self.peek_at_review(step_builder, controls, expected_results, extended_feedback=extended_feedback)
        if extended_feedback and max_attempts == 2:
            self.assertIn(
                "Question 1, Question 2, and Question 4",
                step_builder.find_element_by_css_selector('.correct-list').text
            )

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
        self.html_section(step_builder, controls)
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
        self.html_section(step_builder, controls)
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
        self.html_section(step_builder, controls)
        self.multiple_response_question(None, step_builder, controls, ("Its beauty",), PARTIAL, last=True)

        # The review tips will not be shown because no attempts remain:
        self.assertFalse(review_tips.is_displayed())

    def test_default_messages(self):
        max_attempts = 3
        extended_feedback = False
        params = {
            "max_attempts": max_attempts,
            "extended_feedback": extended_feedback,
        }
        step_builder, controls = self.load_assessment_scenario("step_builder_default_messages.xml", params)

        # First attempt: incomplete (second question wrong)

        # Step 1
        # Submit free-form answer, go to next step
        self.freeform_answer(None, step_builder, controls, 'This is the answer', CORRECT)

        # Step 2
        # Submit MCQ, go to next step
        self.single_choice_question(None, step_builder, controls, 'Maybe not', INCORRECT, last=True)

        # Review step
        expected_results = {
            "correct": 1, "partial": 0, "incorrect": 1, "percentage": 50,
            "num_attempts": 1, "max_attempts": max_attempts
        }
        self.peek_at_review(step_builder, controls, expected_results, extended_feedback=extended_feedback)

        # Should show default message for incomplete submission
        self.assert_message_text(step_builder, "Not quite! You can try again, though.")

        # Try again
        controls.try_again.click()

        self.wait_until_hidden(controls.try_again)
        self.assert_no_message_text(step_builder)

        # Second attempt: complete (both questions correct)

        # Step 1
        # Submit free-form answer, go to next step
        self.freeform_answer(
            None, step_builder, controls, 'This is a different answer', CORRECT, saved_value='This is the answer'
        )
        # Step 2
        # Submit MCQ, go to next step
        self.single_choice_question(None, step_builder, controls, 'Yes', CORRECT, last=True)

        # Review step
        expected_results = {
            "correct": 2, "partial": 0, "incorrect": 0, "percentage": 100,
            "num_attempts": 2, "max_attempts": max_attempts
        }
        self.peek_at_review(step_builder, controls, expected_results, extended_feedback=extended_feedback)

        # Should show default message for complete submission
        self.assert_message_text(step_builder, "Great job!")

        # Try again
        controls.try_again.click()

        self.wait_until_hidden(controls.try_again)
        self.assert_no_message_text(step_builder)

        # Last attempt: complete (both questions correct)

        # Step 1
        # Submit free-form answer, go to next step
        self.freeform_answer(
            None, step_builder, controls, 'This is yet another answer', CORRECT,
            saved_value='This is a different answer'
        )
        # Step 2
        # Submit MCQ, go to next step
        self.single_choice_question(None, step_builder, controls, 'Yes', CORRECT, last=True)

        # Review step
        expected_results = {
            "correct": 2, "partial": 0, "incorrect": 0, "percentage": 100,
            "num_attempts": 3, "max_attempts": max_attempts
        }
        self.peek_at_review(step_builder, controls, expected_results, extended_feedback=extended_feedback)

        # Should show default message for review
        self.assert_message_text(step_builder, "Note: you have used all attempts. Continue to the next unit.")

    def answer_rating_question(self, step_number, question_number, step_builder, question, choice_name):
        question_text = self.question_text(question_number)
        self.wait_until_text_in(question_text, step_builder)
        self.assertIn(question, step_builder.text)
        choices = GetChoices(
            step_builder, 'div[data-name="rating_{}_{}"] > .rating'.format(step_number, question_number)
        )
        choices.select(choice_name)

    def submit_and_go_to_next_step(self, controls):
        controls.submit.click()
        self.wait_until_clickable(controls.next_question)
        controls.next_question.click()

    def plot_controls(self, step_builder):
        class Namespace(object):
            pass

        plot_controls = Namespace()

        plot_controls.default_button = step_builder.find_element_by_css_selector(".plot-default")
        plot_controls.average_button = step_builder.find_element_by_css_selector(".plot-average")
        plot_controls.quadrants_button = step_builder.find_element_by_css_selector(".plot-quadrants")

        return plot_controls

    def plot_empty(self, step_builder):
        points = step_builder.find_elements_by_css_selector("circle")
        self.assertEquals(points, [])

    def check_quadrant_labels(self, step_builder, plot_controls, hidden, labels=['Q1', 'Q2', 'Q3', 'Q4']):
        quadrant_labels = step_builder.find_elements_by_css_selector(".quadrant-label")
        quadrants_button_border_colors = [
            plot_controls.quadrants_button.value_of_css_property('border-top-color'),
            plot_controls.quadrants_button.value_of_css_property('border-right-color'),
            plot_controls.quadrants_button.value_of_css_property('border-bottom-color'),
            plot_controls.quadrants_button.value_of_css_property('border-left-color'),
        ]
        if hidden:
            self.assertEquals(quadrant_labels, [])
            # rgba(255, 0, 0, 1): "red"
            self.assertTrue(all(bc == 'rgba(255, 0, 0, 1)' for bc in quadrants_button_border_colors))
        else:
            self.assertEquals(len(quadrant_labels), 4)
            self.assertEquals(set(label.text for label in quadrant_labels), set(labels))
            # rgba(0, 128, 0, 1): "green"
            self.assertTrue(all(bc == 'rgba(0, 128, 0, 1)' for bc in quadrants_button_border_colors))

    def click_default_button(
        self, plot_controls, overlay_on, color_on='rgba(0, 128, 0, 1)', color_off='rgba(237, 237, 237, 1)'
    ):
        plot_controls.default_button.click()
        default_button_border_colors = [
            plot_controls.default_button.value_of_css_property('border-top-color'),
            plot_controls.default_button.value_of_css_property('border-right-color'),
            plot_controls.default_button.value_of_css_property('border-bottom-color'),
            plot_controls.default_button.value_of_css_property('border-left-color'),
        ]
        if overlay_on:
            self.assertTrue(all(bc == color_on for bc in default_button_border_colors))
        else:
            self.assertTrue(all(bc == color_off for bc in default_button_border_colors))

    def click_average_button(
        self, plot_controls, overlay_on, color_on='rgba(0, 0, 255, 1)', color_off='rgba(237, 237, 237, 1)'
    ):
        plot_controls.average_button.click()
        average_button_border_colors = [
            plot_controls.average_button.value_of_css_property('border-top-color'),
            plot_controls.average_button.value_of_css_property('border-right-color'),
            plot_controls.average_button.value_of_css_property('border-bottom-color'),
            plot_controls.average_button.value_of_css_property('border-left-color'),
        ]
        if overlay_on:
            self.assertTrue(all(bc == color_on for bc in average_button_border_colors))
        else:
            self.assertTrue(all(bc == color_off for bc in average_button_border_colors))

    def test_empty_plot(self):
        step_builder, controls = self.load_assessment_scenario("step_builder_plot_defaults.xml", {})

        # Step 1: Questions
        # Provide first rating
        self.answer_rating_question(1, 1, step_builder, "How much do you agree?", "1 - Disagree")
        # Provide second rating
        self.answer_rating_question(1, 2, step_builder, "How important do you think this is?", "5 - Very important")
        # Advance
        self.submit_and_go_to_next_step(controls)

        # Step 2: Plot
        # Check if plot is empty initially (default overlay on, average overlay off)
        self.plot_empty(step_builder)
        # Obtain references to plot controls
        plot_controls = self.plot_controls(step_builder)
        # Check if plot is empty (default overlay off, average overlay off)
        self.click_default_button(plot_controls, overlay_on=False)
        self.plot_empty(step_builder)
        # Check if plot is empty (default overlay off, average overlay on)
        self.click_average_button(plot_controls, overlay_on=True)
        self.plot_empty(step_builder)
        # Check if plot is empty (default overlay on, average overlay on)
        self.click_default_button(plot_controls, overlay_on=True)
        self.plot_empty(step_builder)
        # Check if plot is empty (default overlay on, average overlay off)
        self.click_average_button(plot_controls, overlay_on=False)
        self.plot_empty(step_builder)
        # Check quadrant labels
        self.check_quadrant_labels(step_builder, plot_controls, hidden=True)
        plot_controls.quadrants_button.click()
        self.check_quadrant_labels(step_builder, plot_controls, hidden=False)

    def check_overlays(self, step_builder, total_num_points, overlays):
        points = step_builder.find_elements_by_css_selector("circle")
        self.assertEquals(len(points), total_num_points)

        for overlay in overlays:
            # Check if correct number of points is present
            points = step_builder.find_elements_by_css_selector(overlay['selector'])
            self.assertEquals(len(points), overlay['num_points'])
            # Check point colors
            point_colors = [
                point.value_of_css_property('fill') for point in points
            ]
            self.assertTrue(all(pc == overlay['point_color'] for pc in point_colors))
            # Check point titles
            point_titles = set([
                point.get_attribute('title') for point in points
            ])
            self.assertEquals(point_titles, set(overlay['titles']))
            # Check positions
            point_positions = set([
                (point.get_attribute('cx'), point.get_attribute('cy')) for point in points
            ])
            self.assertEquals(point_positions, set(overlay['positions']))

    def test_plot(self):
        step_builder, controls = self.load_assessment_scenario("step_builder_plot.xml", {})

        # Step 1: Questions
        # Provide first rating
        self.answer_rating_question(1, 1, step_builder, "How much do you agree?", "1 - Disagree")
        # Provide second rating
        self.answer_rating_question(1, 2, step_builder, "How important do you think this is?", "5 - Very important")
        # Advance
        self.submit_and_go_to_next_step(controls)

        # Step 2: Questions
        # Provide first rating
        self.answer_rating_question(2, 1, step_builder, "How much do you agree?", "5 - Agree")
        # Provide second rating
        self.answer_rating_question(2, 2, step_builder, "How important do you think this is?", "1 - Not important")
        # Advance
        self.submit_and_go_to_next_step(controls)

        # Step 2: Plot
        # Obtain references to plot controls
        plot_controls = self.plot_controls(step_builder)
        # Overlay data
        default_overlay = {
            'selector': '.claim-default',
            'num_points': 2,
            'point_color': 'rgb(255, 165, 0)',  # orange
            'titles': ['2 + 2 = 5: 1, 5', 'The answer to everything is 42: 5, 1'],
            'positions': [
                ('20', '396'),  # Values computed according to xScale and yScale (cf. plot.js)
                ('4', '380'),  # Values computed according to xScale and yScale (cf. plot.js)
            ],
        }
        average_overlay = {
            'selector': '.claim-average',
            'num_points': 2,
            'point_color': 'rgb(128, 0, 128)',  # purple
            'titles': ['2 + 2 = 5: 1, 5', 'The answer to everything is 42: 5, 1'],
            'positions': [
                ('20', '396'),  # Values computed according to xScale and yScale (cf. plot.js)
                ('4', '380'),  # Values computed according to xScale and yScale (cf. plot.js)
            ],
        }
        # Check if plot shows correct overlay(s) initially (default overlay on, average overlay off)
        self.check_overlays(step_builder, total_num_points=2, overlays=[default_overlay])

        # Check if plot shows correct overlay(s) (default overlay on, average overlay on)
        self.click_average_button(plot_controls, overlay_on=True, color_on='rgba(128, 0, 128, 1)')  # purple
        self.check_overlays(step_builder, 4, overlays=[default_overlay, average_overlay])

        # Check if plot shows correct overlay(s) (default overlay off, average overlay on)
        self.click_default_button(plot_controls, overlay_on=False)
        self.check_overlays(step_builder, 2, overlays=[average_overlay])

        # Check if plot shows correct overlay(s) (default overlay off, average overlay off)
        self.click_average_button(plot_controls, overlay_on=False)
        self.plot_empty(step_builder)

        # Check if plot shows correct overlay(s) (default overlay on, average overlay off)
        self.click_default_button(plot_controls, overlay_on=True, color_on='rgba(255, 165, 0, 1)')  # orange
        self.check_overlays(step_builder, 2, overlays=[default_overlay])

        # Check quadrant labels
        self.check_quadrant_labels(step_builder, plot_controls, hidden=True)
        plot_controls.quadrants_button.click()
        self.check_quadrant_labels(
            step_builder, plot_controls, hidden=False,
            labels=['Custom Q1 label', 'Custom Q2 label', 'Custom Q3 label', 'Custom Q4 label']
        )
