import copy
import unittest

from unittest.mock import MagicMock, Mock
from xblock.field_data import DictFieldData

from problem_builder.mentoring import MentoringBlock


class TestFieldMigration(unittest.TestCase):
    """
    Test mentoring fields data migration
    """

    def test_partial_completion_status_migration(self):
        """
        Changed `completed` to `status` in `self.student_results` to accomodate partial responses
        """
        # Instantiate a mentoring block with the old format
        student_results = [
            [u'goal',
                {u'completed': True,
                 u'score': 1,
                 u'student_input': u'test',
                 u'weight': 1}],
            [u'mcq_1_1',
                {u'completed': False,
                 u'score': 0,
                 u'submission': u'maybenot',
                 u'weight': 1}],
        ]
        mentoring = MentoringBlock(MagicMock(), DictFieldData({'student_results': student_results}), Mock())
        self.assertEqual(copy.deepcopy(student_results), mentoring.student_results)

        migrated_student_results = copy.deepcopy(student_results)
        migrated_student_results[0][1]['status'] = 'correct'
        migrated_student_results[1][1]['status'] = 'incorrect'
        del migrated_student_results[0][1]['completed']
        del migrated_student_results[1][1]['completed']
        mentoring.migrate_fields()
        self.assertEqual(migrated_student_results, mentoring.student_results)
