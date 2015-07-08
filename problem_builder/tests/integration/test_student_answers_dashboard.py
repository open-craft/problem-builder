# -*- coding: utf-8 -*-

import time

from mock import patch, Mock
from selenium.common.exceptions import NoSuchElementException
from xblockutils.base_test import SeleniumXBlockTest

from problem_builder.student_answers_dashboard import StudentAnswersDashboardBlock


class MockTasksModule(object):
    """Mock for the tasks module, which can only be meaningfully import in the LMS."""

    def __init__(self, successful=True):
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
        cancel_button = student_answers_dashboard.find_element_by_class_name('data-export-cancel')
        download_button = student_answers_dashboard.find_element_by_class_name('data-export-download')
        delete_button = student_answers_dashboard.find_element_by_class_name('data-export-delete')
        status_area = student_answers_dashboard.find_element_by_class_name('data-export-status')
        info_area = student_answers_dashboard.find_element_by_class_name('data-export-info')

        start_button.click()

        self.wait_until_hidden(start_button)
        self.wait_until_visible(cancel_button)
        self.wait_until_hidden(download_button)
        self.wait_until_hidden(delete_button)
        self.assertIn('The report is currently being generated', status_area.text)

        self.wait_until_visible(start_button)
        self.wait_until_hidden(cancel_button)
        self.wait_until_visible(download_button)
        self.wait_until_visible(delete_button)
        self.assertEqual('', status_area.text)
        self.assertIn('Results retrieved on', info_area.text)

    @patch.dict('sys.modules', {
        'problem_builder.tasks': MockTasksModule(successful=False),
        'instructor_task': True,
        'instructor_task.models': MockInstructorTaskModelsModule(),
    })
    @patch.object(StudentAnswersDashboardBlock, 'user_is_staff', Mock(return_value=True))
    def test_data_export_error(self):
        student_answers_dashboard = self.go_to_view()
        start_button = student_answers_dashboard.find_element_by_class_name('data-export-start')
        cancel_button = student_answers_dashboard.find_element_by_class_name('data-export-cancel')
        download_button = student_answers_dashboard.find_element_by_class_name('data-export-download')
        delete_button = student_answers_dashboard.find_element_by_class_name('data-export-delete')
        status_area = student_answers_dashboard.find_element_by_class_name('data-export-status')
        info_area = student_answers_dashboard.find_element_by_class_name('data-export-info')

        start_button.click()

        self.wait_until_hidden(start_button)
        self.wait_until_visible(cancel_button)
        self.wait_until_hidden(download_button)
        self.wait_until_hidden(delete_button)
        self.assertIn('The report is currently being generated', status_area.text)

        self.wait_until_clickable(start_button)
        self.wait_until_hidden(cancel_button)
        self.wait_until_visible(delete_button)
        self.assertIn('Data export failed. Reason:', status_area.text)
        self.assertEqual('', info_area.text)

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
