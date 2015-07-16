# -*- coding: utf-8 -*-

import re
import time

from mock import patch, Mock
from selenium.common.exceptions import NoSuchElementException
from xblockutils.base_test import SeleniumXBlockTest

from problem_builder.student_answers_dashboard import StudentAnswersDashboardBlock


class MockTasksModule(object):
    """Mock for the tasks module, which can only be meaningfully import in the LMS."""

    def __init__(self, successful=True, display_data=[]):
        self.export_data = Mock()
        async_result = self.export_data.async_result
        async_result.ready.side_effect = [False, False, True, True]
        async_result.id = "export_task_id"
        async_result.successful.return_value = successful
        if successful:
            async_result.result = dict(
                error=None,
                report_filename='/file/report.csv',
                start_timestamp=time.time(),
                generation_time_s=23.4,
                display_data=display_data
            )
        else:
            async_result.result = 'error'
        self.export_data.AsyncResult.return_value = async_result
        self.export_data.delay.return_value = async_result


class MockInstructorTaskModelsModule(object):

    def __init__(self):
        self.ReportStore = Mock()
        self.ReportStore.from_config.return_value.links_for.return_value = [
            ('/file/report.csv', '/url/report.csv')
        ]


class StudentAnswersDashboardTest(SeleniumXBlockTest):

    def setUp(self):
        super(StudentAnswersDashboardTest, self).setUp()
        self.set_scenario_xml("""
        <vertical_demo>
          <pb-student-answers-dashboard url_name="data_export"/>
        </vertical_demo>
        """)

    def test_students_dont_see_interface(self):
        data_export = self.go_to_view()
        self.assertIn('This interface can only be used by course staff.', data_export.text)

    @patch.dict('sys.modules', {
        'problem_builder.tasks': MockTasksModule(successful=True),
        'instructor_task': True,
        'instructor_task.models': MockInstructorTaskModelsModule(),
    })
    @patch.object(StudentAnswersDashboardBlock, 'user_is_staff', Mock(return_value=True))
    def test_data_export_success(self):
        student_answers_dashboard = self.go_to_view()
        start_button = student_answers_dashboard.find_element_by_class_name('data-export-start')
        result_block = student_answers_dashboard.find_element_by_class_name('data-export-results')
        info_area = student_answers_dashboard.find_element_by_class_name('data-export-info')
        status_area = student_answers_dashboard.find_element_by_class_name('data-export-status')
        download_button = student_answers_dashboard.find_element_by_class_name('data-export-download')
        cancel_button = student_answers_dashboard.find_element_by_class_name('data-export-cancel')
        delete_button = student_answers_dashboard.find_element_by_class_name('data-export-delete')

        start_button.click()

        self.wait_until_hidden(start_button)
        self.wait_until_hidden(result_block)
        self.wait_until_hidden(download_button)
        self.wait_until_visible(cancel_button)
        self.wait_until_hidden(delete_button)
        self.assertIn('The report is currently being generated', status_area.text)

        self.wait_until_visible(start_button)
        self.wait_until_visible(result_block)
        self.wait_until_visible(download_button)
        self.wait_until_hidden(cancel_button)
        self.wait_until_visible(delete_button)
        for column in [
                'Section', 'Subsection', 'Unit',
                'Type', 'Question', 'Answer', 'Username'
        ]:
            self.assertIn(column, result_block.text)
        self.assertIn('Results retrieved on', info_area.text)
        self.assertEqual('', status_area.text)

    @patch.dict('sys.modules', {
        'problem_builder.tasks': MockTasksModule(successful=False),
        'instructor_task': True,
        'instructor_task.models': MockInstructorTaskModelsModule(),
    })
    @patch.object(StudentAnswersDashboardBlock, 'user_is_staff', Mock(return_value=True))
    def test_data_export_error(self):
        student_answers_dashboard = self.go_to_view()
        start_button = student_answers_dashboard.find_element_by_class_name('data-export-start')
        result_block = student_answers_dashboard.find_element_by_class_name('data-export-results')
        info_area = student_answers_dashboard.find_element_by_class_name('data-export-info')
        status_area = student_answers_dashboard.find_element_by_class_name('data-export-status')
        download_button = student_answers_dashboard.find_element_by_class_name('data-export-download')
        cancel_button = student_answers_dashboard.find_element_by_class_name('data-export-cancel')
        delete_button = student_answers_dashboard.find_element_by_class_name('data-export-delete')

        start_button.click()

        self.wait_until_hidden(start_button)
        self.wait_until_hidden(result_block)
        self.wait_until_visible(cancel_button)
        self.wait_until_hidden(download_button)
        self.wait_until_hidden(delete_button)
        self.assertIn('The report is currently being generated', status_area.text)

        self.wait_until_visible(start_button)
        self.wait_until_hidden(cancel_button)
        self.wait_until_visible(delete_button)
        self.assertFalse(result_block.is_displayed())
        self.assertEqual('', info_area.text)
        self.assertIn('Data export failed. Reason:', status_area.text)

    @patch.dict('sys.modules', {
        'problem_builder.tasks': MockTasksModule(successful=True),
        'instructor_task': True,
        'instructor_task.models': MockInstructorTaskModelsModule(),
    })
    @patch.object(StudentAnswersDashboardBlock, 'user_is_staff', Mock(return_value=True))
    def test_pagination_no_results(self):
        student_answers_dashboard = self.go_to_view()
        start_button = student_answers_dashboard.find_element_by_class_name('data-export-start')
        result_block = student_answers_dashboard.find_element_by_class_name('data-export-results')
        first_page_button = student_answers_dashboard.find_element_by_id('first-page')
        prev_page_button = student_answers_dashboard.find_element_by_id('prev-page')
        next_page_button = student_answers_dashboard.find_element_by_id('next-page')
        last_page_button = student_answers_dashboard.find_element_by_id('last-page')
        current_page_info = student_answers_dashboard.find_element_by_id('current-page')
        total_pages_info = student_answers_dashboard.find_element_by_id('total-pages')

        start_button.click()

        self.wait_until_visible(result_block)

        self.assertFalse(first_page_button.is_enabled())
        self.assertFalse(prev_page_button.is_enabled())
        self.assertFalse(next_page_button.is_enabled())
        self.assertFalse(last_page_button.is_enabled())

        self.assertEqual('0', current_page_info.text)
        self.assertEqual('0', total_pages_info.text)

    @patch.dict('sys.modules', {
        'problem_builder.tasks': MockTasksModule(
            successful=True, display_data=[[
                'Test section', 'Test subsection', 'Test unit',
                'Test type', 'Test question', 'Test answer', 'Test username'
            ]]),
        'instructor_task': True,
        'instructor_task.models': MockInstructorTaskModelsModule(),
    })
    @patch.object(StudentAnswersDashboardBlock, 'user_is_staff', Mock(return_value=True))
    def test_pagination_single_result(self):
        student_answers_dashboard = self.go_to_view()
        start_button = student_answers_dashboard.find_element_by_class_name('data-export-start')
        result_block = student_answers_dashboard.find_element_by_class_name('data-export-results')
        first_page_button = student_answers_dashboard.find_element_by_id('first-page')
        prev_page_button = student_answers_dashboard.find_element_by_id('prev-page')
        next_page_button = student_answers_dashboard.find_element_by_id('next-page')
        last_page_button = student_answers_dashboard.find_element_by_id('last-page')
        current_page_info = student_answers_dashboard.find_element_by_id('current-page')
        total_pages_info = student_answers_dashboard.find_element_by_id('total-pages')

        start_button.click()

        self.wait_until_visible(result_block)

        for contents in [
                'Test section', 'Test subsection', 'Test unit',
                'Test type', 'Test question', 'Test answer', 'Test username'
        ]:
            self.assertIn(contents, result_block.text)

        self.assertFalse(first_page_button.is_enabled())
        self.assertFalse(prev_page_button.is_enabled())
        self.assertFalse(next_page_button.is_enabled())
        self.assertFalse(last_page_button.is_enabled())

        self.assertEqual('1', current_page_info.text)
        self.assertEqual('1', total_pages_info.text)

    @patch.dict('sys.modules', {
        'problem_builder.tasks': MockTasksModule(
            successful=True, display_data=[[
                'Test section', 'Test subsection', 'Test unit',
                'Test type', 'Test question', 'Test answer', 'Test username'
            ] for _ in range(45)]),
        'instructor_task': True,
        'instructor_task.models': MockInstructorTaskModelsModule(),
    })
    @patch.object(StudentAnswersDashboardBlock, 'user_is_staff', Mock(return_value=True))
    def test_pagination_multiple_results(self):
        student_answers_dashboard = self.go_to_view()
        start_button = student_answers_dashboard.find_element_by_class_name('data-export-start')
        result_block = student_answers_dashboard.find_element_by_class_name('data-export-results')
        first_page_button = student_answers_dashboard.find_element_by_id('first-page')
        prev_page_button = student_answers_dashboard.find_element_by_id('prev-page')
        next_page_button = student_answers_dashboard.find_element_by_id('next-page')
        last_page_button = student_answers_dashboard.find_element_by_id('last-page')
        current_page_info = student_answers_dashboard.find_element_by_id('current-page')
        total_pages_info = student_answers_dashboard.find_element_by_id('total-pages')

        start_button.click()

        self.wait_until_visible(result_block)

        for contents in [
                'Test section', 'Test subsection', 'Test unit',
                'Test type', 'Test question', 'Test answer', 'Test username'
        ]:
            occurrences = re.findall(contents, result_block.text)
            self.assertEqual(len(occurrences), 15)

        self.assertFalse(first_page_button.is_enabled())
        self.assertFalse(prev_page_button.is_enabled())
        self.assertTrue(next_page_button.is_enabled())
        self.assertTrue(last_page_button.is_enabled())

        self.assertEqual('1', current_page_info.text)
        self.assertEqual('3', total_pages_info.text)

        # Test behavior of pagination controls

        # - "Next" button

        next_page_button.click()  # Navigate to second page

        self.assertTrue(first_page_button.is_enabled())
        self.assertTrue(prev_page_button.is_enabled())
        self.assertTrue(next_page_button.is_enabled())
        self.assertTrue(last_page_button.is_enabled())

        self.assertEqual('2', current_page_info.text)

        next_page_button.click()  # Navigate to third page

        self.assertTrue(first_page_button.is_enabled())
        self.assertTrue(prev_page_button.is_enabled())
        self.assertFalse(next_page_button.is_enabled())
        self.assertFalse(last_page_button.is_enabled())

        self.assertEqual('3', current_page_info.text)

        # - "Prev" button

        prev_page_button.click()  # Navigate to second page

        self.assertTrue(first_page_button.is_enabled())
        self.assertTrue(prev_page_button.is_enabled())
        self.assertTrue(next_page_button.is_enabled())
        self.assertTrue(last_page_button.is_enabled())

        self.assertEqual('2', current_page_info.text)

        prev_page_button.click()  # Navigate to first page

        self.assertFalse(first_page_button.is_enabled())
        self.assertFalse(prev_page_button.is_enabled())
        self.assertTrue(next_page_button.is_enabled())
        self.assertTrue(last_page_button.is_enabled())

        self.assertEqual('1', current_page_info.text)

        # - "Last" button

        last_page_button.click()  # Navigate to last page

        self.assertTrue(first_page_button.is_enabled())
        self.assertTrue(prev_page_button.is_enabled())
        self.assertFalse(next_page_button.is_enabled())
        self.assertFalse(last_page_button.is_enabled())

        self.assertEqual('3', current_page_info.text)

        # - "First" button

        first_page_button.click()  # Navigate to first page

        self.assertFalse(first_page_button.is_enabled())
        self.assertFalse(prev_page_button.is_enabled())
        self.assertTrue(next_page_button.is_enabled())
        self.assertTrue(last_page_button.is_enabled())

        self.assertEqual('1', current_page_info.text)

    def test_non_staff_disabled(self):
        student_answers_dashboard = self.go_to_view()
        self.assertRaises(
            NoSuchElementException, student_answers_dashboard.find_element_by_class_name, 'data-export-start'
        )
        self.assertRaises(
            NoSuchElementException, student_answers_dashboard.find_element_by_class_name, 'data-export-cancel'
        )
        self.assertRaises(
            NoSuchElementException, student_answers_dashboard.find_element_by_class_name, 'data-export-download'
        )
        self.assertRaises(
            NoSuchElementException, student_answers_dashboard.find_element_by_class_name, 'data-export-delete'
        )
        self.assertRaises(
            NoSuchElementException, student_answers_dashboard.find_element_by_class_name, 'data-export-results'
        )
        self.assertRaises(
            NoSuchElementException, student_answers_dashboard.find_element_by_class_name, 'data-export-status'
        )
