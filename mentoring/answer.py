# -*- coding: utf-8 -*-


# Imports ###########################################################

import logging

from xblock.core import XBlock
from xblock.fields import Any, Scope
from xblock.fragment import Fragment

from .models import Answer
from .utils import load_resource


# Globals ###########################################################

log = logging.getLogger(__name__)


# Classes ###########################################################

class AnswerBlock(XBlock):
    """
    A field where the student enters an answer

    Must be included as a child of a mentoring block. Answers are persisted as django model instances
    to make them searchable and referenceable across xblocks.
    """
    student_input = Any(help="Last input submitted by the student", default="", scope=Scope.user_state)

    def __init__(self, *args, **kwargs):
        super(AnswerBlock, self).__init__(*args, **kwargs)
        if self.name:
            self.student_input = self.get_model_object().student_input
    
    def student_view(self, context=None):  # pylint: disable=W0613
        """Returns default student view."""
        return Fragment(u"<p>I can only appear inside problems.</p>")

    def mentoring_view(self, context=None):
        html = u'<textarea cols="100" rows="10" maxlength="{}" name="input">{}</textarea>'.format(
                Answer._meta.get_field('student_input').max_length,
                self.student_input)
        
        fragment = Fragment(html)
        fragment.add_javascript(load_resource('static/js/answer.js'))
        fragment.initialize_js('AnswerBlock')
        return fragment

    def submit(self, submission):
        self.student_input = submission[0]['value']
        log.info(u'Answer submitted for`{}`: "{}"'.format(self.name, self.student_input))
        return self.student_input

    def save(self):
        """
        Replicate data changes on the related Django model used for sharing of data accross XBlocks
        """
        super(AnswerBlock, self).save()
        answer_data = self.get_model_object()
        if answer_data.student_input != self.student_input:
            answer_data.student_input = self.student_input
            answer_data.save()

    def get_model_object(self):
        if not self.name:
            raise ValueError, 'AnswerBlock.name field need to be set to a non-null/empty value'

        # TODO Use a random user id
        student_id = self.scope_ids.user_id

        answer_data, created = Answer.objects.get_or_create(
            student_id=student_id,
            name=self.name
        )
        return answer_data
