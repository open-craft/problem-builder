import unittest
import ddt
from mock import Mock
from problem_builder.mentoring import MentoringWithExplicitStepsBlock

from .utils import ScoresTestMixin, instantiate_block


@ddt.ddt
class TestStepBuilder(ScoresTestMixin, unittest.TestCase):
    """ Unit tests for Step Builder (MentoringWithExplicitStepsBlock) """

    def test_scores(self):
        """
        Test that scores are emitted correctly.
        """
        # Submit an empty block - score should be 0:
        block = instantiate_block(MentoringWithExplicitStepsBlock)
        with self.expect_score_event(block, score=0.0, max_score=1.0):
            request = Mock(method="POST", body="{}")
            block.publish_attempt(request, suffix=None)

        # Mock a block to contain an MCQ question, then submit it. Score should be 1:
        block = instantiate_block(MentoringWithExplicitStepsBlock)
        block.questions = [Mock(weight=1.0)]
        block.questions[0].name = 'mcq1'
        block.steps = [Mock(
            student_results=[('mcq1', {'score': 1, 'status': 'correct'})]
        )]
        block.answer_mapper = lambda _status: None
        with self.expect_score_event(block, score=1.0, max_score=1.0):
            request = Mock(method="POST", body="{}")
            block.publish_attempt(request, suffix=None)
