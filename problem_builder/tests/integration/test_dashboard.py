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
import json
from functools import wraps
from textwrap import dedent
from unittest.mock import Mock, patch

from selenium.common.exceptions import NoSuchElementException

from .base_test import ProblemBuilderBaseTest


class MockSubmissionsAPI:
    """
    Mock the submissions API, since it's not available in the test environment.
    """
    def __init__(self):
        self.submissions = {}

    def dict_to_key(self, dict_key):
        return (dict_key['student_id'], dict_key['course_id'], dict_key['item_id'], dict_key['item_type'])

    def create_submission(self, dict_key, submission):
        record = dict(
            student_item=dict_key,
            attempt_number=Mock(),
            submitted_at=Mock(),
            created_at=Mock(),
            answer=submission,
        )
        self.submissions[self.dict_to_key(dict_key)] = record
        return record

    def get_submissions(self, key, limit=1):
        assert limit == 1
        key = self.dict_to_key(key)
        if key in self.submissions:
            return [self.submissions[key]]
        return []


def check_dashboard_and_report(fixture, set_mentoring_values=True, **kwargs):
    """
    Decorator for dashboard test methods.

    - Sets up the given fixture
    - Runs the decorated test
    - Clicks the download link
    - Opens the report
    - Runs the decorated test again against the report

    Any extra keyword arguments are passed to the dashboard XBlock.
    """
    def wrapper(test):
        @wraps(test)
        def wrapped(test_case):
            test_case._install_fixture(fixture)
            if kwargs:
                dashboard = test_case.vertical.get_child('test-scenario.pb-dashboard.d0.u0')
                for key, value in kwargs.items():
                    setattr(dashboard, key, value)
                dashboard.save()
            if set_mentoring_values:
                test_case._set_mentoring_values()
            test_case.go_to_view('student_view')
            test(test_case)
            download_link = test_case.browser.find_element_by_css_selector('.report-download-link')
            download_link.click()
            test_case.browser.get(download_link.get_attribute('href'))
            test_case.assertRegexpMatches(test_case.browser.current_url, r'^data:text/html;base64,')
            test(test_case)
        return wrapped
    return wrapper


class TestDashboardBlock(ProblemBuilderBaseTest):
    """
    Test the Student View of a dashboard XBlock linked to some problem builder blocks
    """
    SIMPLE_DASHBOARD = """<pb-dashboard mentoring_ids='["dummy-value"]'/>"""
    ALTERNATIVE_DASHBOARD = dedent("""
    <pb-dashboard mentoring_ids='["dummy-value"]' show_numbers="false"
        average_labels='{"Step 1": "Avg.", "Step 2":"Mean", "Step 3":"Second Quartile"}'
        header_html='&lt;p id="header-paragraph"&gt;Header&lt;/p&gt;'
        footer_html='&lt;p id="footer-paragraph"&gt;Footer&lt;/p&gt;'
    />
    """)
    HIDE_QUESTIONS_DASHBOARD = dedent("""
    <pb-dashboard mentoring_ids='["dummy-value"]'
        exclude_questions='{"Step 1": [2, 3], "Step 2":[3], "Step 3":[2]}'
    />
    """)
    MALFORMED_HIDE_QUESTIONS_DASHBOARD = dedent("""
    <pb-dashboard mentoring_ids='["dummy-value"]'
      exclude_questions='{"Step 1": "1234", "Step 2":[3], "Step 3":[2]}'
    />
    """)

    # Clean up screenshots if the tests pass
    cleanup_on_success = True

    def setUp(self):
        super().setUp()

        # Apply a whole bunch of patches that are needed in lieu of the LMS/CMS runtime and edx-submissions:

        def get_mentoring_blocks(dashboard_block, mentoring_ids, ignore_errors=True):
            return [dashboard_block.runtime.get_block(key) for key in dashboard_block.get_parent().children[:-1]]

        mock_submisisons_api = MockSubmissionsAPI()
        patches = (
            (
                "problem_builder.dashboard.DashboardBlock._get_submission_key",
                lambda _, child_id: dict(student_id="student", course_id="course", item_id=child_id, item_type="pb-mcq")
            ),
            (
                "problem_builder.sub_api.SubmittingXBlockMixin.student_item_key",
                property(lambda block: dict(
                    student_id="student", course_id="course", item_id=block.scope_ids.usage_id, item_type="pb-mcq"
                ))
            ),
            ("problem_builder.dashboard.DashboardBlock.get_mentoring_blocks", get_mentoring_blocks),
            ("problem_builder.dashboard.sub_api", mock_submisisons_api),
            ("problem_builder.mcq.sub_api", mock_submisisons_api),
            (
                "problem_builder.mentoring.MentoringBlock.url_name",
                property(lambda block: block.display_name)
            )
        )
        for p in patches:
            patcher = patch(*p)
            patcher.start()
            self.addCleanup(patcher.stop)

    def _install_fixture(self, dashboard_xml):
        self.load_scenario("dashboard.xml", {'dashboard': dashboard_xml}, load_immediately=True)
        self.vertical = self.load_root_xblock()

    def _get_cell_contents(self, cell):
        try:
            visible_text = cell.find_element_by_css_selector('span:not(.sr)').text
        except NoSuchElementException:
            visible_text = ""
        screen_reader_text = cell.find_element_by_css_selector('span.sr')
        return visible_text, screen_reader_text.text

    def _assert_cell_contents(self, cell, expected_visible_text, expected_screen_reader_text):
        visible_text, screen_reader_text = self._get_cell_contents(cell)
        self.assertEqual(visible_text, expected_visible_text)
        self.assertEqual(screen_reader_text, expected_screen_reader_text)

    def _format_sr_text(self, visible_text):
        return f"Score: {visible_text}"

    def _set_mentoring_values(self):
        pbs = self.browser.find_elements_by_css_selector('.mentoring')
        for pb in pbs:
            mcqs = pb.find_elements_by_css_selector('fieldset.choices')
            for idx, mcq in enumerate(mcqs):
                choices = mcq.find_elements_by_css_selector('.choices .choice label')
                choices[idx].click()
            self.click_submit(pb)

    @check_dashboard_and_report(SIMPLE_DASHBOARD, set_mentoring_values=False)
    def test_empty_dashboard(self):
        """
        Test that when the student has not submitted any question answers, we still see
        the dashboard, and its lists all the MCQ questions in the way we expect.
        """
        dashboard = self.browser.find_element_by_css_selector('.pb-dashboard')
        step_headers = dashboard.find_elements_by_css_selector('thead')
        self.assertEqual(len(step_headers), 3)
        self.assertEqual([hdr.text for hdr in step_headers], ["Step 1", "Step 2", "Step 3"])
        steps = dashboard.find_elements_by_css_selector('tbody')
        self.assertEqual(len(steps), 3)

        for step in steps:
            mcq_rows = step.find_elements_by_css_selector('tr')
            self.assertTrue(2 <= len(mcq_rows) <= 3)
            for mcq in mcq_rows:
                cell = mcq.find_element_by_css_selector('td:last-child')
                self._assert_cell_contents(cell, '', 'No value yet')

    @check_dashboard_and_report(SIMPLE_DASHBOARD)
    def test_dashboard(self):
        """
        Submit an answer to each MCQ, then check that the dashboard reflects those answers.
        """
        dashboard = self.browser.find_element_by_css_selector('.pb-dashboard')
        headers = dashboard.find_elements_by_class_name('report-header')
        self.assertEqual(len(headers), 0)
        footers = dashboard.find_elements_by_class_name('report-footer')
        self.assertEqual(len(footers), 0)
        steps = dashboard.find_elements_by_css_selector('tbody')
        self.assertEqual(len(steps), 3)
        expected_values = ('1', '2', '3', '4', 'B')

        for step_num, step in enumerate(steps):
            mcq_rows = step.find_elements_by_css_selector('tr:not(.avg-row)')
            self.assertTrue(2 <= len(mcq_rows) <= 3)
            for mcq in mcq_rows:
                cell = mcq.find_element_by_css_selector('td.value')
                visible_text, screen_reader_text = self._get_cell_contents(cell)
                self.assertIn(visible_text, expected_values)
                self.assertIn(screen_reader_text, map(self._format_sr_text, expected_values))
            # Check the average:
            avg_row = step.find_element_by_css_selector('tr.avg-row')
            left_col = avg_row.find_element_by_css_selector('.desc')
            self.assertEqual(left_col.text, "Average")
            right_col = avg_row.find_element_by_css_selector('.value')
            expected_average = {0: "2", 1: "3", 2: "1"}[step_num]
            self._assert_cell_contents(right_col, expected_average, self._format_sr_text(expected_average))

    @check_dashboard_and_report(SIMPLE_DASHBOARD, visual_rules=json.dumps({
        'background': '/static/test/swoop-bg.png',
    }))
    def test_dashboard_image(self):
        """
        Test that the dashboard image is displayed correctly, both on the page
        and it the report. We allow minor differences here as the report
        screenshot is not a perfect match.
        """
        self.assertScreenshot('.pb-dashboard-visual svg', 'dashboard-image', threshold=3000)

    @check_dashboard_and_report(SIMPLE_DASHBOARD, visual_rules=json.dumps({
        'background': ('//raw.githubusercontent.com/open-craft/problem-builder/master/'
                       'problem_builder/static/test/swoop-bg.png'),
    }))
    def test_dashboard_image_cross_domain(self):
        """
        Test that cross-domain dashboard images are displayed correctly. We
        allow minor differences here as the report screenshot is not a perfect
        match.
        """
        self.assertScreenshot('.pb-dashboard-visual svg', 'dashboard-image', threshold=3000)

    @check_dashboard_and_report(
        SIMPLE_DASHBOARD,
        visual_rules=json.dumps({
            'background': '/static/test/swoop-bg.png',
            'images': [
                '/static/test/swoop-step1.png',
                '/static/test/swoop-step2.png',
            ],
        }),
        color_rules='\n'.join([
            '0: grey',
            'x <= 2: #aa2626',
            'x <= 3: #e7ce76',
            '#84b077',
        ]),
    )
    def test_dashboard_image_overlay(self):
        """
        Test that image overlays are displayed correctly on the dashboard.
        """
        self.assertScreenshot('.pb-dashboard-visual svg', 'dashboard-image-overlay', threshold=3000)

    @check_dashboard_and_report(ALTERNATIVE_DASHBOARD)
    def test_dashboard_alternative(self):
        """
        Submit an answer to each MCQ, then check that the dashboard reflects those answers with alternative
        configuration:

        * Average label is "Avg." instead of default "Average"
        * Numerical values are not shown
        * Include HTML header and footer snippets
        """
        dashboard = self.browser.find_element_by_css_selector('.pb-dashboard')
        header_p = dashboard.find_element_by_id('header-paragraph')
        self.assertEqual(header_p.text, 'Header')
        footer_p = dashboard.find_element_by_id('footer-paragraph')
        self.assertEqual(footer_p.text, 'Footer')
        steps = dashboard.find_elements_by_css_selector('tbody')
        self.assertEqual(len(steps), 3)

        average_labels = ["Avg.", "Mean", "Second Quartile"]

        expected_values = ('1', '2', '3', '4', 'B')

        for step_num, step in enumerate(steps):
            mcq_rows = step.find_elements_by_css_selector('tr:not(.avg-row)')
            self.assertTrue(2 <= len(mcq_rows) <= 3)
            for mcq in mcq_rows:
                cell = mcq.find_element_by_css_selector('td.value')
                visible_text, screen_reader_text = self._get_cell_contents(cell)
                # this dashboard configured to not show numbers
                self.assertEqual(visible_text, '')
                # but screen reader content still added
                self.assertIn(screen_reader_text, map(self._format_sr_text, expected_values))
            # Check the average:
            avg_row = step.find_element_by_css_selector('tr.avg-row')
            left_col = avg_row.find_element_by_css_selector('.desc')
            self.assertEqual(left_col.text, average_labels[step_num])
            right_col = avg_row.find_element_by_css_selector('.value')
            expected_average = {0: "2", 1: "3", 2: "1"}[step_num]
            self._assert_cell_contents(right_col, '', self._format_sr_text(expected_average))

    @check_dashboard_and_report(HIDE_QUESTIONS_DASHBOARD)
    def test_dashboard_exclude_questions(self):
        """
        Submit an answer to each MCQ, then check that the dashboard ignores questions it is configured to ignore
        """
        dashboard = self.browser.find_element_by_css_selector('.pb-dashboard')
        steps = dashboard.find_elements_by_css_selector('tbody')
        self.assertEqual(len(steps), 3)
        expected_values = ('1', '2', '3', '4')

        lengths = [1, 2, 1]

        for step_num, step in enumerate(steps):
            mcq_rows = step.find_elements_by_css_selector('tr:not(.avg-row)')
            self.assertEqual(len(mcq_rows), lengths[step_num])
            for mcq in mcq_rows:
                cell = mcq.find_element_by_css_selector('td.value')
                visible_text, screen_reader_text = self._get_cell_contents(cell)
                self.assertIn(visible_text, expected_values)
                self.assertIn(screen_reader_text, map(self._format_sr_text, expected_values))
            # Check the average:
            avg_row = step.find_element_by_css_selector('tr.avg-row')
            left_col = avg_row.find_element_by_css_selector('.desc')
            self.assertEqual(left_col.text, "Average")
            right_col = avg_row.find_element_by_css_selector('.value')
            expected_average = {0: "1", 1: "3", 2: "1"}[step_num]
            self._assert_cell_contents(right_col, expected_average, self._format_sr_text(expected_average))

    @check_dashboard_and_report(MALFORMED_HIDE_QUESTIONS_DASHBOARD)
    def test_dashboard_malformed_exclude_questions(self):
        """
        Submit an answer to each MCQ, then check that the dashboard ignores questions it is configured to ignore
        """
        dashboard = self.browser.find_element_by_css_selector('.pb-dashboard')
        steps = dashboard.find_elements_by_css_selector('tbody')
        self.assertEqual(len(steps), 3)

        expected_values = ('1', '2', '3', '4')

        lengths = [3, 2, 1]

        for step_num, step in enumerate(steps):
            mcq_rows = step.find_elements_by_css_selector('tr:not(.avg-row)')
            self.assertEqual(len(mcq_rows), lengths[step_num])
            for mcq in mcq_rows:
                cell = mcq.find_element_by_css_selector('td.value')
                visible_text, screen_reader_text = self._get_cell_contents(cell)
                self.assertIn(visible_text, expected_values)
                self.assertIn(screen_reader_text, map(self._format_sr_text, expected_values))
            # Check the average:
            avg_row = step.find_element_by_css_selector('tr.avg-row')
            left_col = avg_row.find_element_by_css_selector('.desc')
            self.assertEqual(left_col.text, "Average")
            right_col = avg_row.find_element_by_css_selector('.value')
            expected_average = {0: "2", 1: "3", 2: "1"}[step_num]
            self._assert_cell_contents(right_col, expected_average, self._format_sr_text(expected_average))
