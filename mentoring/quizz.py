# -*- coding: utf-8 -*-


# Imports ###########################################################

import copy
import logging

from xblock.core import XBlock
from xblock.fields import List, Scope, String
from xblock.fragment import Fragment

from .utils import load_resource, render_template


# Globals ###########################################################

log = logging.getLogger(__name__)


# Functions #########################################################

def commas_to_list(commas_str):
    """
    Converts a comma-separated string to a list
    """
    if commas_str is None:
        return None # Means default value (which can be non-empty)
    elif commas_str == '':
        return [] # Means empty list
    else:
        return commas_str.split(',')


# Classes ###########################################################

class QuizzBlock(XBlock):
    """
    TODO: Description
    """
    question = String(help="Question to ask the student", scope=Scope.content, default="")
    type = String(help="Type of quizz", scope=Scope.content, default="yes-no-unsure")
    low = String(help="Label for low ratings", scope=Scope.content, default="Less")
    high = String(help="Label for high ratings", scope=Scope.content, default="More")
    tip = String(help="Mentoring tip to provide if needed", scope=Scope.content, default="")
    display = List(help="List of choices to display the tip for", scope=Scope.content, default=None)
    reject = List(help="List of choices to reject", scope=Scope.content, default=None)
    student_choice = String(help="Last input submitted by the student", default="", scope=Scope.user_state)

    @classmethod
    def parse_xml(cls, node, runtime, keys):
        block = runtime.construct_xblock_from_class(cls, keys)

        for child in node:
            if child.tag == "question":
                block.question = child.text
            elif child.tag == "tip":
                block.tip = child.text
                block.reject = commas_to_list(child.get('reject'))
                block.display = commas_to_list(child.get('display'))
            else:
                block.runtime.add_node_as_child(block, child)

        for name, value in node.items():
            if name in block.fields:
                setattr(block, name, value)

        return block

    def student_view(self, context=None):  # pylint: disable=W0613
        """Returns default student view."""
        return Fragment(u"<p>I can only appear inside mentoring blocks.</p>")

    def mentoring_view(self, context=None):
        if self.type not in ('yes-no-unsure', 'rating'):
            raise ValueError, u'Invalid value for QuizzBlock.type: `{}`'.format(self.type)

        template_path = 'templates/html/quizz_{}.html'.format(self.type)
        html = render_template(template_path, {
            'self': self,
        })

        fragment = Fragment(html)
        fragment.add_css(load_resource('static/css/quizz.css'))
        fragment.add_javascript(load_resource('static/js/quizz.js'))
        fragment.initialize_js('QuizzBlock')
        return fragment

    def submit(self, submission):
        log.debug(u'Received quizz submission: "%s"', submission)

        completed = self.is_completed(submission)
        show_tip = self.is_tip_shown(submission)
        self.student_choice = submission

        if show_tip:
            formatted_tip = render_template('templates/html/tip.html', {
                'self': self,
            })
        else:
            formatted_tip = ''

        result = {
            'submission': submission,
            'completed': completed,
            'tip': formatted_tip,
        }
        log.debug(u'Quizz submission result: %s', result)
        return result

    def is_completed(self, submission):
        return submission and submission not in self.reject_with_defaults

    def is_tip_shown(self, submission):
        return not submission or submission in self.display_with_defaults

    @property
    def reject_with_defaults(self):
        if self.reject is None:
            if self.type == 'yes-no-unsure':
                return ['no', 'unsure']
            elif self.type == 'rating':
                return ['1', '2', '3']
        else:
            return self.reject

    @property
    def display_with_defaults(self):
        display = copy.copy(self.display)
        if display is None:
            display = self.reject_with_defaults
        else:
            display += [choice for choice in self.reject_with_defaults
                               if choice not in display]
        return display
