# -*- coding: utf-8 -*-


# Imports ###########################################################

import logging

from xblock.fragment import Fragment
from xblock.problem import TextInputBlock


# Globals ###########################################################

log = logging.getLogger(__name__)


# Classes ###########################################################

class AnswerBlock(TextInputBlock):
    """
    A field where the student enters an answer

    Must be included as a child of a mentoring block. Answers are persisted as django model instances
    to make them searchable and referenceable across xblocks.
    """
    
    def mentoring_view(self, context):
        # TODO: Not implemented
        return Fragment(u'<textarea cols="100" rows="10"></textarea>')
