# -*- coding: utf-8 -*-

import time
import pdb
import sys

from mock import patch, Mock
from xblockutils.base_test import SeleniumXBlockTest

from problem_builder.data_export import DataExportBlock


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
                generation_time_s = 23.4,
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


class DataExportTest(SeleniumXBlockTest):

    def setUp(self):
        super(DataExportTest, self).setUp()
        self.set_scenario_xml("""
        <vertical_demo>
          <pb-data-export url_name="data_export"/>
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
    @patch.object(DataExportBlock, 'user_is_staff', Mock(return_value=True))
    def test_data_export(self):
        data_export = self.go_to_view()
        start_button = data_export.find_element_by_class_name('data-export-start')
        cancel_button = data_export.find_element_by_class_name('data-export-cancel')
        download_button = data_export.find_element_by_class_name('data-export-download')
        delete_button = data_export.find_element_by_class_name('data-export-delete')
        status_area = data_export.find_element_by_class_name('data-export-status')

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
        self.assertIn('A report is available for download.', status_area.text)
