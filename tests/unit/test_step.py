import unittest

from lxml import etree

from mentoring import MentoringBlock
import mentoring
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
