# -*- coding: utf-8 -*-
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
from mock import Mock, patch
from xblockutils.base_test import SeleniumXBlockTest


class MockSubmissionsAPI(object):
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


class TestDashboardBlock(SeleniumXBlockTest):
    """
    Test the Student View of a dashboard XBlock linked to some problem builder blocks
    """
    def setUp(self):
        super(TestDashboardBlock, self).setUp()
        # Set up our scenario:
        self.set_scenario_xml("""
            <vertical_demo>
                <problem-builder display_name="Step 1">
                    <pb-mcq display_name="1.1 First MCQ" question="Which option?" correct_choices='["1","2","3","4"]'>
                        <pb-choice value="1">Option 1</pb-choice>
                        <pb-choice value="2">Option 2</pb-choice>
                        <pb-choice value="3">Option 3</pb-choice>
                        <pb-choice value="4">Option 4</pb-choice>
                    </pb-mcq>
                    <pb-mcq display_name="1.2 Second MCQ" question="Which option?" correct_choices='["1","2","3","4"]'>
                        <pb-choice value="1">Option 1</pb-choice>
                        <pb-choice value="2">Option 2</pb-choice>
                        <pb-choice value="3">Option 3</pb-choice>
                        <pb-choice value="4">Option 4</pb-choice>
                    </pb-mcq>
                    <pb-mcq display_name="1.3 Third MCQ" question="Which option?" correct_choices='["1","2","3","4"]'>
                        <pb-choice value="1">Option 1</pb-choice>
                        <pb-choice value="2">Option 2</pb-choice>
                        <pb-choice value="3">Option 3</pb-choice>
                        <pb-choice value="4">Option 4</pb-choice>
                    </pb-mcq>
                    <html_demo> This message here should be ignored. </html_demo>
                </problem-builder>
                <problem-builder display_name="Step 2">
                    <pb-mcq display_name="2.1 First MCQ" question="Which option?" correct_choices='["1","2","3","4"]'>
                        <pb-choice value="4">Option 4</pb-choice>
                        <pb-choice value="5">Option 5</pb-choice>
                        <pb-choice value="6">Option 6</pb-choice>
                    </pb-mcq>
                    <pb-mcq display_name="2.2 Second MCQ" question="Which option?" correct_choices='["1","2","3","4"]'>
                        <pb-choice value="1">Option 1</pb-choice>
                        <pb-choice value="2">Option 2</pb-choice>
                        <pb-choice value="3">Option 3</pb-choice>
                        <pb-choice value="4">Option 4</pb-choice>
                    </pb-mcq>
                    <pb-mcq display_name="2.3 Third MCQ" question="Which option?" correct_choices='["1","2","3","4"]'>
                        <pb-choice value="1">Option 1</pb-choice>
                        <pb-choice value="2">Option 2</pb-choice>
                        <pb-choice value="3">Option 3</pb-choice>
                        <pb-choice value="4">Option 4</pb-choice>
                    </pb-mcq>
                </problem-builder>
                <problem-builder display_name="Step 3">
                    <pb-mcq display_name="3.1 First MCQ" question="Which option?" correct_choices='["1","2","3","4"]'>
                        <pb-choice value="1">Option 1</pb-choice>
                        <pb-choice value="2">Option 2</pb-choice>
                        <pb-choice value="3">Option 3</pb-choice>
                        <pb-choice value="4">Option 4</pb-choice>
                    </pb-mcq>
                    <pb-mcq display_name="3.2 MCQ with non-numeric values"
                      question="Which option?" correct_choices='["1","2","3","4"]'>
                        <pb-choice value="A">Option A</pb-choice>
                        <pb-choice value="B">Option B</pb-choice>
                        <pb-choice value="C">Option C</pb-choice>
                    </pb-mcq>
                </problem-builder>
                <pb-dashboard mentoring_ids='["dummy-value"]'>
                </pb-dashboard>
            </vertical_demo>
        """)

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
            ("problem_builder.mcq.sub_api", mock_submisisons_api)
        )
        for p in patches:
            patcher = patch(*p)
            patcher.start()
            self.addCleanup(patcher.stop)
        # All the patches are installed; now we can proceed with using the XBlocks for tests:
        self.go_to_view("student_view")
        self.vertical = self.load_root_xblock()

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
                value = mcq.find_element_by_css_selector('td:last-child')
                self.assertEqual(value.text, '')

    def test_dashboard(self):
        """
        Submit an answer to each MCQ, then check that the dashboard reflects those answers.
        """
        pbs = self.browser.find_elements_by_css_selector('.mentoring')
        for pb in pbs:
            mcqs = pb.find_elements_by_css_selector('fieldset.choices')
            for idx, mcq in enumerate(mcqs):
                choices = mcq.find_elements_by_css_selector('.choices .choice label')
                choices[idx].click()
            submit = pb.find_element_by_css_selector('.submit input.input-main')
            self.assertTrue(submit.is_enabled())
            submit.click()
            self.wait_until_disabled(submit)

        # Reload the page:
        self.go_to_view("student_view")
        dashboard = self.browser.find_element_by_css_selector('.pb-dashboard')
        steps = dashboard.find_elements_by_css_selector('tbody')
        self.assertEqual(len(steps), 3)

        for step_num, step in enumerate(steps):
            mcq_rows = step.find_elements_by_css_selector('tr:not(.avg-row)')
            self.assertTrue(2 <= len(mcq_rows) <= 3)
            for mcq in mcq_rows:
                value = mcq.find_element_by_css_selector('td.value')
                self.assertIn(value.text, ('1', '2', '3', '4', 'B'))
            # Check the average:
            avg_row = step.find_element_by_css_selector('tr.avg-row')
            left_col = avg_row.find_element_by_css_selector('.desc')
            self.assertEqual(left_col.text, "Average")
            right_col = avg_row.find_element_by_css_selector('.value')
            expected_average = {0: "2", 1: "3", 2: "1"}[step_num]
            self.assertEqual(right_col.text, expected_average)
