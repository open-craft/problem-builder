import math
import re
import time
from unittest.mock import Mock, patch

from selenium.common.exceptions import NoSuchElementException
from xblockutils.base_test import SeleniumXBlockTest

from problem_builder.instructor_tool import PAGE_SIZE, InstructorToolBlock


class MockTasksModule:
    """Mock for the tasks module, which can only be meaningfully import in the LMS."""

    def __init__(self, successful=True, display_data=[], delay=0):
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

        def produce_result(*args):
            time.sleep(delay)
            return async_result

        self.export_data.AsyncResult.side_effect = produce_result
        self.export_data.delay.side_effect = produce_result


class MockInstructorTaskModelsModule:

    def __init__(self):
        self.ReportStore = Mock()
        self.ReportStore.from_config.return_value.links_for.return_value = [
            ('/file/report.csv', '/url/report.csv')
        ]


class InstructorToolTest(SeleniumXBlockTest):

    def setUp(self):
        super().setUp()
        self.set_scenario_xml("""
        <vertical_demo>
          <pb-instructor-tool url_name="data_export"/>
          <problem-builder>
            <pb-answer name="answer" question="Is this a long long long long long long long long long long question?" />
          </problem-builder>
        </vertical_demo>
        """)

    def test_students_dont_see_interface(self):
        data_export = self.go_to_view()
        self.assertIn('This interface can only be used by course staff.', data_export.text)

    @patch.dict('sys.modules', {
        'problem_builder.tasks': MockTasksModule(successful=True),
        'lms': True,
        'lms.djangoapps': True,
        'lms.djangoapps.instructor_task': True,
        'lms.djangoapps.instructor_task.models': MockInstructorTaskModelsModule(),
    })
    @patch.object(InstructorToolBlock, 'user_is_staff', Mock(return_value=True))
    def test_export_field_container_width(self):
        instructor_tool = self.go_to_view()

        export_field_container = instructor_tool.find_element_by_class_name('data-export-field-container')
        parent_div = export_field_container.find_element_by_xpath('..')

        export_field_container_width = export_field_container.size['width']
        parent_div_width = parent_div.size['width']

        self.assertTrue(export_field_container_width <= math.ceil(0.43 * parent_div_width))

    @patch.dict('sys.modules', {
        'problem_builder.tasks': MockTasksModule(successful=True),
        'lms': True,
        'lms.djangoapps': True,
        'lms.djangoapps.instructor_task': True,
        'lms.djangoapps.instructor_task.models': MockInstructorTaskModelsModule(),
    })
    @patch.object(InstructorToolBlock, 'user_is_staff', Mock(return_value=True))
    def test_root_block_select_width(self):
        instructor_tool = self.go_to_view()

        root_block_select = instructor_tool.find_element_by_name('root_block_id')
        parent_div = root_block_select.find_element_by_xpath('../..')

        root_block_select_width = root_block_select.size['width']
        parent_div_width = parent_div.size['width']

        self.assertTrue(root_block_select_width <= math.ceil(0.55 * parent_div_width))

    @patch.dict('sys.modules', {
        'problem_builder.tasks': MockTasksModule(successful=True),
        'lms': True,
        'lms.djangoapps': True,
        'lms.djangoapps.instructor_task': True,
        'lms.djangoapps.instructor_task.models': MockInstructorTaskModelsModule(),
    })
    @patch.object(InstructorToolBlock, 'user_is_staff', Mock(return_value=True))
    def test_data_export_delete(self):
        instructor_tool = self.go_to_view()
        start_button = instructor_tool.find_element_by_class_name('data-export-start')
        result_block = instructor_tool.find_element_by_class_name('data-export-results')
        status_area = instructor_tool.find_element_by_class_name('data-export-status')
        download_button = instructor_tool.find_element_by_class_name('data-export-download')
        cancel_button = instructor_tool.find_element_by_class_name('data-export-cancel')
        delete_button = instructor_tool.find_element_by_class_name('data-export-delete')

        self.wait_until_clickable(start_button)
        start_button.click()

        self.wait_until_visible(result_block)
        self.wait_until_visible(delete_button)

        delete_button.click()

        self.wait_until_hidden(result_block)
        self.wait_until_hidden(delete_button)

        self.assertTrue(start_button.is_enabled())
        self.assertEqual('', status_area.text)
        self.assertFalse(download_button.is_displayed())
        self.assertFalse(cancel_button.is_displayed())

    @patch.dict('sys.modules', {
        'problem_builder.tasks': MockTasksModule(successful=True),
        'lms': True,
        'lms.djangoapps': True,
        'lms.djangoapps.instructor_task': True,
        'lms.djangoapps.instructor_task.models': MockInstructorTaskModelsModule(),
    })
    @patch.object(InstructorToolBlock, 'user_is_staff', Mock(return_value=True, delay=1))
    def test_data_export_success(self):
        instructor_tool = self.go_to_view()
        start_button = instructor_tool.find_element_by_class_name('data-export-start')
        result_block = instructor_tool.find_element_by_class_name('data-export-results')
        info_area = instructor_tool.find_element_by_class_name('data-export-info')
        status_area = instructor_tool.find_element_by_class_name('data-export-status')
        download_button = instructor_tool.find_element_by_class_name('data-export-download')
        cancel_button = instructor_tool.find_element_by_class_name('data-export-cancel')
        delete_button = instructor_tool.find_element_by_class_name('data-export-delete')

        self.wait_until_clickable(start_button)
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
        time.sleep(1)

        for column in [
                'Section', 'Subsection', 'Unit',
                'Type', 'Question', 'Answer', 'Username'
        ]:
            self.assertIn(column, result_block.text)
        self.assertIn('Results retrieved on', info_area.text)
        self.assertEqual('', status_area.text)

    @patch.dict('sys.modules', {
        'problem_builder.tasks': MockTasksModule(successful=False, delay=1),
        'lms': True,
        'lms.djangoapps': True,
        'lms.djangoapps.instructor_task': True,
        'lms.djangoapps.instructor_task.models': MockInstructorTaskModelsModule(),
    })
    @patch.object(InstructorToolBlock, 'user_is_staff', Mock(return_value=True))
    def test_data_export_error(self):
        instructor_tool = self.go_to_view()
        start_button = instructor_tool.find_element_by_class_name('data-export-start')
        result_block = instructor_tool.find_element_by_class_name('data-export-results')
        info_area = instructor_tool.find_element_by_class_name('data-export-info')
        status_area = instructor_tool.find_element_by_class_name('data-export-status')
        download_button = instructor_tool.find_element_by_class_name('data-export-download')
        cancel_button = instructor_tool.find_element_by_class_name('data-export-cancel')
        delete_button = instructor_tool.find_element_by_class_name('data-export-delete')

        self.wait_until_clickable(start_button)
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
        'lms': True,
        'lms.djangoapps': True,
        'lms.djangoapps.instructor_task': True,
        'lms.djangoapps.instructor_task.models': MockInstructorTaskModelsModule(),
    })
    @patch.object(InstructorToolBlock, 'user_is_staff', Mock(return_value=True))
    def test_pagination_no_results(self):
        instructor_tool = self.go_to_view()
        start_button = instructor_tool.find_element_by_class_name('data-export-start')
        result_block = instructor_tool.find_element_by_class_name('data-export-results')
        first_page_button = instructor_tool.find_element_by_id('first-page')
        prev_page_button = instructor_tool.find_element_by_id('prev-page')
        next_page_button = instructor_tool.find_element_by_id('next-page')
        last_page_button = instructor_tool.find_element_by_id('last-page')
        current_page_info = instructor_tool.find_element_by_id('current-page')
        total_pages_info = instructor_tool.find_element_by_id('total-pages')

        self.wait_until_clickable(start_button)
        start_button.click()

        self.wait_until_visible(result_block)
        time.sleep(1)  # Allow some time for result block to fully fade in

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
        'lms': True,
        'lms.djangoapps': True,
        'lms.djangoapps.instructor_task': True,
        'lms.djangoapps.instructor_task.models': MockInstructorTaskModelsModule(),
    })
    @patch.object(InstructorToolBlock, 'user_is_staff', Mock(return_value=True))
    def test_pagination_single_result(self):
        instructor_tool = self.go_to_view()
        start_button = instructor_tool.find_element_by_class_name('data-export-start')
        result_block = instructor_tool.find_element_by_class_name('data-export-results')
        first_page_button = instructor_tool.find_element_by_id('first-page')
        prev_page_button = instructor_tool.find_element_by_id('prev-page')
        next_page_button = instructor_tool.find_element_by_id('next-page')
        last_page_button = instructor_tool.find_element_by_id('last-page')
        current_page_info = instructor_tool.find_element_by_id('current-page')
        total_pages_info = instructor_tool.find_element_by_id('total-pages')

        self.wait_until_clickable(start_button)
        start_button.click()

        self.wait_until_visible(result_block)
        time.sleep(1)  # Allow some time for result block to fully fade in

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
            ] for _ in range(PAGE_SIZE*3)]),
        'lms': True,
        'lms.djangoapps': True,
        'lms.djangoapps.instructor_task': True,
        'lms.djangoapps.instructor_task.models': MockInstructorTaskModelsModule(),
    })
    @patch.object(InstructorToolBlock, 'user_is_staff', Mock(return_value=True))
    def test_pagination_multiple_results(self):
        instructor_tool = self.go_to_view()
        start_button = instructor_tool.find_element_by_class_name('data-export-start')
        result_block = instructor_tool.find_element_by_class_name('data-export-results')
        first_page_button = instructor_tool.find_element_by_id('first-page')
        prev_page_button = instructor_tool.find_element_by_id('prev-page')
        next_page_button = instructor_tool.find_element_by_id('next-page')
        last_page_button = instructor_tool.find_element_by_id('last-page')
        current_page_info = instructor_tool.find_element_by_id('current-page')
        total_pages_info = instructor_tool.find_element_by_id('total-pages')

        self.wait_until_clickable(start_button)
        start_button.click()

        self.wait_until_visible(result_block)
        time.sleep(1)  # Allow some time for result block to fully fade in

        for contents in [
                'Test section', 'Test subsection', 'Test unit',
                'Test type', 'Test question', 'Test answer', 'Test username'
        ]:
            occurrences = re.findall(contents, result_block.text)
            self.assertEqual(len(occurrences), PAGE_SIZE)

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
        instructor_tool = self.go_to_view()
        self.assertRaises(
            NoSuchElementException, instructor_tool.find_element_by_class_name, 'data-export-start'
        )
        self.assertRaises(
            NoSuchElementException, instructor_tool.find_element_by_class_name, 'data-export-cancel'
        )
        self.assertRaises(
            NoSuchElementException, instructor_tool.find_element_by_class_name, 'data-export-download'
        )
        self.assertRaises(
            NoSuchElementException, instructor_tool.find_element_by_class_name, 'data-export-delete'
        )
        self.assertRaises(
            NoSuchElementException, instructor_tool.find_element_by_class_name, 'data-export-results'
        )
        self.assertRaises(
            NoSuchElementException, instructor_tool.find_element_by_class_name, 'data-export-status'
        )
