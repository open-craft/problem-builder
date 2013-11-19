# -*- coding: utf-8 -*-


# Imports ###########################################################

import logging

from xblock.core import XBlock
from xblock.fields import Any, Scope
from xblock.fragment import Fragment


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
    
    def student_view(self, context=None):  # pylint: disable=W0613
        """Returns default student view."""
        return Fragment(u"<p>I can only appear inside problems.</p>")

    def mentoring_view(self, context=None):
        html = u'<textarea cols="100" rows="10" name="input">{}</textarea>'.format(self.student_input)
        fragment = Fragment(html)
        fragment.add_javascript("""
            function AnswerBlock(runtime, element) {
                return {
                    submit: function() {
                        return $(element).find(':input').serializeArray();
                    },
                    handleSubmit: function(result) {
                        $(element).find('.message').text((result || {}).error || '');
                    }
                }
            }
            """)
        fragment.initialize_js('AnswerBlock')
        return fragment

    def submit(self, submission):
        self.student_input = submission[0]['value']
        log.info(u'Answer submitted for`{}`: "{}"'.format(self.name, self.student_input))
        return self.student_input

