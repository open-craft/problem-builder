import copy
import unittest
from mock import MagicMock, Mock

from xblock.field_data import DictFieldData

from mentoring import MentoringBlock
from mentoring.step import StepMixin, StepParentMixin


class Parent(StepParentMixin):
    def get_children_objects(self):
        return list(self._children)

    def _set_children_for_test(self, *children):
        self._children = children
        for child in self._children:
            try:
                child.parent = self
            except AttributeError:
                pass


class Step(StepMixin):
    def __init__(self):
        pass


class NotAStep(object):
    pass


class TestStepMixin(unittest.TestCase):
    def test_single_step_is_returned_correctly(self):
        block = Parent()
        step = Step()
        block._children = [step]

        self.assertSequenceEqual(block.steps, [step])

    def test_only_steps_are_returned(self):
        block = Parent()
        step1 = Step()
        step2 = Step()
        block._set_children_for_test(step1, 1, "2", "Step", NotAStep(), False, step2, NotAStep())

        self.assertSequenceEqual(block.steps, [step1, step2])

    def test_proper_number_is_returned_for_step(self):
        block = Parent()
        step1 = Step()
        step2 = Step()
        block._set_children_for_test(step1, 1, "2", "Step", NotAStep(), False, step2, NotAStep())

        self.assertEquals(step1.step_number, 1)
        self.assertEquals(step2.step_number, 2)

    def test_the_number_does_not_represent_the_order_of_creation(self):
        block = Parent()
        step1 = Step()
        step2 = Step()
        block._set_children_for_test(step2, 1, "2", "Step", NotAStep(), False, step1, NotAStep())

        self.assertEquals(step1.step_number, 2)
        self.assertEquals(step2.step_number, 1)

    def test_lonely_step_is_true_for_stand_alone_steps(self):
        block = Parent()
        step1 = Step()
        block._set_children_for_test(1, "2", step1, "Step", NotAStep(), False)

        self.assertTrue(step1.lonely_step)

    def test_lonely_step_is_true_if_parent_have_more_steps(self):
        block = Parent()
        step1 = Step()
        step2 = Step()
        block._set_children_for_test(1, step2, "2", step1, "Step", NotAStep(), False)

        self.assertFalse(step1.lonely_step)
        self.assertFalse(step2.lonely_step)


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
            [ u'goal',
                {   u'completed': True,
                    u'score': 1,
                    u'student_input': u'test',
                    u'weight': 1}],
            [ u'mcq_1_1',
                {   u'completed': False,
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
