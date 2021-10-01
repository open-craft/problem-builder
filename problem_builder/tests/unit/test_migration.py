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
            ['goal',
                {'completed': True,
                 'score': 1,
                 'student_input': 'test',
                 'weight': 1}],
            ['mcq_1_1',
                {'completed': False,
                 'score': 0,
                 'submission': 'maybenot',
                 'weight': 1}],
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
