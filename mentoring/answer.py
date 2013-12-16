# -*- coding: utf-8 -*-


# Imports ###########################################################

import logging

from xblock.core import XBlock
from xblock.fields import Boolean, Scope, String
from xblock.fragment import Fragment

from .models import Answer
from .utils import load_resource, render_template


# Globals ###########################################################

log = logging.getLogger(__name__)


# Classes ###########################################################

class AnswerBlock(XBlock):
    """
    A field where the student enters an answer

    Must be included as a child of a mentoring block. Answers are persisted as django model instances
    to make them searchable and referenceable across xblocks.
    """
    student_input = String(help="Last input submitted by the student", default="", scope=Scope.user_state)
    read_only = Boolean(help="Display as a read-only field", default=False, scope=Scope.content)
    default_from = String(help="If specified, the name of the answer to get the default value from",
                          default=None, scope=Scope.content)

    def __init__(self, *args, **kwargs):
        super(AnswerBlock, self).__init__(*args, **kwargs)

        # Only attempt to locate a model object for this block when the answer has a name
        if self.name:
            self.student_input = self.get_model_object().student_input

        # Default value can be set from another answer's current value
        if not self.student_input and self.default_from:
            self.student_input = self.get_model_object(name=self.default_from).student_input
    
    def student_view(self, context=None):  # pylint: disable=W0613
        """Returns default student view."""
        return Fragment(u"<p>I can only appear inside mentoring blocks.</p>")

    def mentoring_view(self, context=None):
        if not self.read_only:
            html = render_template('templates/html/answer_editable.html', {
                'self': self,
                'max_length': Answer._meta.get_field('student_input').max_length,
            })
        else:
            html = render_template('templates/html/answer_read_only.html', {
                'self': self,
            })
        
        fragment = Fragment(html)
        fragment.add_css(load_resource('static/css/answer.css'))
        fragment.add_javascript(load_resource('static/js/answer.js'))
        fragment.initialize_js('AnswerBlock')
        return fragment

    def mentoring_table_view(self, context=None):
        html = render_template('templates/html/answer_table.html', {
            'self': self,
        })
        fragment = Fragment(html)
        fragment.add_css(load_resource('static/css/answer_table.css'))
        return fragment

    def submit(self, submission):
        if not self.read_only:
            self.student_input = submission[0]['value'].strip()
            log.info(u'Answer submitted for`{}`: "{}"'.format(self.name, self.student_input))
        return {
            'student_input': self.student_input,
            'completed': bool(self.student_input),
        }

    def save(self):
        """
        Replicate data changes on the related Django model used for sharing of data accross XBlocks
        """
        super(AnswerBlock, self).save()
        answer_data = self.get_model_object()
        if answer_data.student_input != self.student_input and not self.read_only:
            answer_data.student_input = self.student_input
            answer_data.save()

    def get_model_object(self, name=None):
        """
        Fetches the Answer model object for the answer named `name`
        """
        # By default, get the model object for the current answer's name
        if not name:
            name = self.name
        # Consistency check - we should have a name by now
        if not name:
            raise ValueError, 'AnswerBlock.name field need to be set to a non-null/empty value'

        # TODO Use anonymous_user_id
        student_id = self.scope_ids.user_id

        answer_data, created = Answer.objects.get_or_create(
            student_id=student_id,
            name=name
        )
        return answer_data
