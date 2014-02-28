# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Harvard
#
# Authors:
#          Xavier Antoviaque <xavier@antoviaque.org>
#
# This software's license gives you freedom; you can copy, convey,
# propagate, redistribute and/or modify this program under the terms of
# the GNU Affero General Public License (AGPL) as published by the Free
# Software Foundation (FSF), either version 3 of the License, or (at your
# option) any later version of the AGPL published by the FSF.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program in a file in the toplevel directory called
# "AGPLv3".  If not, see <http://www.gnu.org/licenses/>.
#

# Imports ###########################################################

import logging

from xblock.fragment import Fragment

from .light_children import LightChild, Scope, String
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

class QuizzBlock(LightChild):
    """
    An XBlock used to ask multiple-choice questions

    Must be a child of a MentoringBlock. Allow to display a tip/advice depending on the 
    values entered by the student, and supports multiple types of multiple-choice
    set, with preset choices and author-defined values.
    """
    question = String(help="Question to ask the student", scope=Scope.content, default="")
    type = String(help="Type of quizz", scope=Scope.content, default="choices")
    student_choice = String(help="Last input submitted by the student", default="", scope=Scope.user_state)
    low = String(help="Label for low ratings", scope=Scope.content, default="Less")
    high = String(help="Label for high ratings", scope=Scope.content, default="More")

    @classmethod
    def init_block_from_node(cls, block, node, attr):
        block.light_children = []
        for child_id, xml_child in enumerate(node):
            if xml_child.tag == "question":
                block.question = xml_child.text
            else:
                cls.add_node_as_child(block, xml_child, child_id)

        for name, value in attr:
            setattr(block, name, value)

        return block

    def mentoring_view(self, context=None):
        if str(self.type) not in ('rating', 'choices'):
            raise ValueError, u'Invalid value for QuizzBlock.type: `{}`'.format(self.type)

        template_path = 'templates/html/quizz_{}.html'.format(self.type)
        html = render_template(template_path, {
            'self': self,
            'custom_choices': self.custom_choices,
        })

        fragment = Fragment(html)
        fragment.add_css(load_resource('static/css/quizz.css'))
        fragment.add_javascript(load_resource('static/js/quizz.js'))
        fragment.initialize_js('QuizzBlock')
        return fragment

    @property
    def custom_choices(self):
        custom_choices = []
        for child in self.get_children_objects():
            if isinstance(child, QuizzChoiceBlock):
                custom_choices.append(child)
        return custom_choices

    def submit(self, submission):
        log.debug(u'Received quizz submission: "%s"', submission)

        completed = True
        tips_fragments = []
        for tip in self.get_tips():
            completed = completed and tip.is_completed(submission)
            if tip.is_tip_displayed(submission):
                tips_fragments.append(tip.render(submission))

        formatted_tips = render_template('templates/html/tip_group.html', {
            'self': self,
            'tips_fragments': tips_fragments,
            'submission': submission,
            'submission_display': self.get_submission_display(submission),
        })

        self.student_choice = submission
        result = {
            'submission': submission,
            'completed': completed,
            'tips': formatted_tips,
        }
        log.debug(u'Quizz submission result: %s', result)
        return result

    def get_submission_display(self, submission):
        """
        Get the human-readable version of a submission value
        """
        for choice in self.custom_choices:
            if choice.value == submission:
                return choice.content
        return submission

    def get_tips(self):
        """
        Returns the tips contained in this block
        """
        tips = []
        for child in self.get_children_objects():
            if isinstance(child, QuizzTipBlock):
                tips.append(child)
        return tips


class QuizzTipBlock(LightChild):
    """
    Each quizz
    """
    content = String(help="Text of the tip to provide if needed", scope=Scope.content, default="")
    display = String(help="List of choices to display the tip for", scope=Scope.content, default=None)
    reject = String(help="List of choices to reject", scope=Scope.content, default=None)
    
    def render(self, submission):
        """
        Returns a fragment containing the formatted tip
        """
        fragment, named_children = self.get_children_fragment({})
        fragment.add_content(render_template('templates/html/tip.html', {
            'self': self,
            'named_children': named_children,
        }))
        return fragment

    def is_completed(self, submission):
        return submission and submission not in self.reject_with_defaults

    def is_tip_displayed(self, submission):
        return submission in self.display_with_defaults

    @property
    def display_with_defaults(self):
        display = commas_to_list(self.display)
        if display is None:
            display = self.reject_with_defaults
        else:
            display += [choice for choice in self.reject_with_defaults
                               if choice not in display]
        return display

    @property
    def reject_with_defaults(self):
        reject = commas_to_list(self.reject)
        log.debug(reject)
        return reject or []


class QuizzChoiceBlock(LightChild):
    """
    Custom choice of an answer for a quizz
    """
    value = String(help="Value of the choice when selected", scope=Scope.content, default="")
    content = String(help="Human-readable version of the choice value", scope=Scope.content, default="")
