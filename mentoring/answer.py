# -*- coding: utf-8 -*-

import logging

from xblock.problem import TextInputBlock

log = logging.getLogger(__name__)


class AnswerBlock(TextInputBlock):
    """
    A field where the student enters an answer

    Must be included as a child of a mentoring block. Answers are persisted as django model instances
    to make them searchable and referenceable across xblocks.
    """
    pass
