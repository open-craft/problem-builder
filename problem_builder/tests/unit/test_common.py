"""
Tests common to Problem Builder and Step Builder
"""
import ddt
import unittest
from problem_builder.mentoring import MentoringBlock, MentoringWithExplicitStepsBlock
from xblock.core import XBlock

from .utils import ScoresTestMixin, instantiate_block


@ddt.ddt
class TestBuilderBlocks(ScoresTestMixin, unittest.TestCase):
    """ Unit tests for Problem Builder and Step Builder """

    @ddt.data(MentoringBlock, MentoringWithExplicitStepsBlock)
    def test_interface(self, block_cls):
        """
        Basic tests of the block's public interface.
        """
        self.assertTrue(issubclass(block_cls, XBlock))
        self.assertTrue(block_cls.has_children)

        block = instantiate_block(block_cls)
        self.assertTrue(block.has_children)
        self.assert_produces_scores(block)
