import unittest
from xblock.field_data import DictFieldData
from problem_builder.step import MentoringStepBlock

from problem_builder.mixins import QuestionMixin, StepParentMixin
from mock import Mock, patch


class Parent(StepParentMixin):
    @property
    def children(self):
        """ Return an ID for each of our chilren"""
        return range(0, len(self._children))

    @property
    def runtime(self):
        return Mock(
            get_block=lambda i: self._children[i],
            load_block_type=lambda i: type(self._children[i]),
            id_reader=Mock(get_definition_id=lambda i: i, get_block_type=lambda i: i)
        )

    def _set_children_for_test(self, *children):
        self._children = children
        for idx, child in enumerate(self._children):
            try:
                child.get_parent = lambda: self
                child.scope_ids = Mock(usage_id=idx)
            except AttributeError:
                pass


class BaseClass(object):
    pass


class Step(BaseClass, QuestionMixin):
    def __init__(self):
        pass


class NotAStep(object):
    pass


class TestQuestionMixin(unittest.TestCase):
    def test_single_step_is_returned_correctly(self):
        block = Parent()
        step = Step()
        block._children = [step]

        steps = [block.runtime.get_block(cid) for cid in block.step_ids]
        self.assertSequenceEqual(steps, [step])

    def test_only_steps_are_returned(self):
        block = Parent()
        step1 = Step()
        step2 = Step()
        block._set_children_for_test(step1, 1, "2", "Step", NotAStep(), False, step2, NotAStep())

        steps = [block.runtime.get_block(cid) for cid in block.step_ids]
        self.assertSequenceEqual(steps, [step1, step2])

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

    def test_lonely_child_is_true_for_stand_alone_steps(self):
        block = Parent()
        step1 = Step()
        block._set_children_for_test(1, "2", step1, "Step", NotAStep(), False)

        self.assertTrue(step1.lonely_child)

    def test_lonely_child_is_true_if_parent_have_more_steps(self):
        block = Parent()
        step1 = Step()
        step2 = Step()
        block._set_children_for_test(1, step2, "2", step1, "Step", NotAStep(), False)

        self.assertFalse(step1.lonely_child)
        self.assertFalse(step2.lonely_child)


class TestMentoringStep(unittest.TestCase):

    def get_allowed_blocks(self, block):
        return [
            getattr(allowed_block, 'category', getattr(allowed_block, 'CATEGORY', None))
            for allowed_block in block.allowed_nested_blocks
        ]

    def test_allowed_nested_blocks(self):
        block = MentoringStepBlock(Mock(), DictFieldData({}), Mock())
        self.assertEqual(
            self.get_allowed_blocks(block),
            [
                'pb-answer',
                'pb-mcq',
                'pb-rating',
                'pb-mrq',
                'pb-completion',
                'html',
                'pb-answer-recap',
                'pb-table',
                'sb-plot',
                'pb-slider',
            ]
        )
        from sys import modules
        xmodule_mock = Mock()
        fake_modules = {
            'xmodule': xmodule_mock,
            'xmodule.video_module': xmodule_mock.video_module,
            'xmodule.video_module.video_module': xmodule_mock.video_module.video_module,
            'imagemodal': Mock()
        }
        with patch.dict(modules, fake_modules):
            self.assertEqual(
                self.get_allowed_blocks(block), [
                    'pb-answer',
                    'pb-mcq',
                    'pb-rating',
                    'pb-mrq',
                    'pb-completion',
                    'html',
                    'pb-answer-recap',
                    'pb-table',
                    'sb-plot',
                    'pb-slider',
                    'video',
                    'imagemodal',
                ]
            )
