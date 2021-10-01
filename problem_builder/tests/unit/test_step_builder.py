import unittest
from unittest.mock import Mock

from xblock.field_data import DictFieldData

from problem_builder.mentoring import MentoringWithExplicitStepsBlock
from problem_builder.step import MentoringStepBlock
from problem_builder.step_review import (ConditionalMessageBlock,
                                         ReviewStepBlock, ScoreSummaryBlock)

from .utils import BlockWithChildrenTestMixin


class TestMentoringBlock(BlockWithChildrenTestMixin, unittest.TestCase):
    def test_student_view_data(self):
        blocks_by_id = {}

        services_mocks = {
            "i18n": Mock(ugettext=lambda string: string)
        }

        mock_runtime = Mock(
            get_block=lambda block_id: blocks_by_id[block_id],
            load_block_type=lambda block: block.__class__,
            service=lambda _, service_id: services_mocks.get(service_id),
            id_reader=Mock(
                get_definition_id=lambda block_id: block_id,
                get_block_type=lambda block_id: blocks_by_id[block_id],
            ),
        )

        def make_block(block_type, data, **kwargs):
            usage_id = str(make_block.id_counter)
            make_block.id_counter += 1
            mock_scope_ids = Mock(usage_id=usage_id)
            block = block_type(
                mock_runtime,
                field_data=DictFieldData(data),
                scope_ids=mock_scope_ids,
                **kwargs
            )
            block.category = 'test'
            blocks_by_id[usage_id] = block
            parent = kwargs.get('for_parent')
            if parent:
                parent.children.append(usage_id)
                block.parent = parent.scope_ids.usage_id
            return block
        make_block.id_counter = 1

        # Create top-level Step Builder block.
        step_builder_data = {
            'display_name': 'My Step Builder',
            'show_title': False,
            'weight': 5.0,
            'max_attempts': 3,
            'extended_feedback': True,
        }
        step_builder = make_block(MentoringWithExplicitStepsBlock, step_builder_data)

        # Create a 'Step' block (as child of 'Step Builder') and add two mock children to it.
        # One of the mocked children implements `student_view_data`, while the other one does not.
        child_a = Mock(spec=['student_view_data'])
        child_a.category = 'test'
        child_a.scope_ids = Mock(usage_id='child_a')
        child_a.student_view_data.return_value = 'child_a_json'
        blocks_by_id['child_a'] = child_a

        child_b = Mock(spec=[])
        child_b.scope_ids = Mock(usage_id='child_b')
        child_b.category = 'test'
        blocks_by_id['child_b'] = child_b

        step_data = {
            'display_name': 'First Step',
            'show_title': True,
            'next_button_label': 'Next Question',
            'message': 'This is the message.',
            'children': [child_a.scope_ids.usage_id, child_b.scope_ids.usage_id],
        }
        make_block(MentoringStepBlock, step_data, for_parent=step_builder)

        # Create a 'Step Review' block (as child of 'Step Builder').
        review_step_data = {
            'display_name': 'My Review Step',
        }
        review_step = make_block(ReviewStepBlock, review_step_data, for_parent=step_builder)

        # Create 'Score Summary' block as child of 'Step Review'.
        make_block(ScoreSummaryBlock, {}, for_parent=review_step)

        # Create 'Conditional Message' block as child of 'Step Review'.
        conditional_message_data = {
            'content': 'This message is conditional',
            'score_condition': 'perfect',
            'num_attempts_condition': 'can_try_again',
        }
        make_block(ConditionalMessageBlock, conditional_message_data, for_parent=review_step)

        expected = {
            'block_id': '1',
            'display_name': step_builder_data['display_name'],
            'title': step_builder_data['display_name'],
            'show_title': step_builder_data['show_title'],
            'weight': step_builder_data['weight'],
            'max_attempts': step_builder_data['max_attempts'],
            'extended_feedback': step_builder_data['extended_feedback'],
            'components': [
                {
                    'block_id': '2',
                    'type': 'sb-step',
                    'display_name': step_data['display_name'],
                    'title': step_data['display_name'],
                    'show_title': step_data['show_title'],
                    'next_button_label': step_data['next_button_label'],
                    'message': step_data['message'],
                    'components': ['child_a_json'],
                },
                {
                    'block_id': '3',
                    'type': 'sb-review-step',
                    'display_name': review_step_data['display_name'],
                    'title': review_step_data['display_name'],
                    'components': [
                        {
                            'block_id': '4',
                            'display_name': "Score Summary",
                            'type': 'sb-review-score',
                        },
                        {
                            'block_id': '5',
                            'display_name': "Conditional Message",
                            'type': 'sb-conditional-message',
                            'content': conditional_message_data['content'],
                            'score_condition': conditional_message_data['score_condition'],
                            'num_attempts_condition': conditional_message_data['num_attempts_condition'],
                        },
                    ],
                },
            ],
        }
        self.assertEqual(step_builder.student_view_data(), expected)
