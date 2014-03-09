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

from .choice import ChoiceBlock
from .light_children import LightChild, Scope, String
from .tip import TipBlock
from .utils import render_template


# Globals ###########################################################

log = logging.getLogger(__name__)


# Classes ###########################################################

class QuestionnaireAbstractBlock(LightChild):
    """
    An abstract class used for MCQ/MRQ blocks

    Must be a child of a MentoringBlock. Allow to display a tip/advice depending on the
    values entered by the student, and supports multiple types of multiple-choice
    set, with preset choices and author-defined values.
    """
    question = String(help="Question to ask the student", scope=Scope.content, default="")

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
        name = self.__class__.__name__

        if str(self.type) not in self.valid_types:
            raise ValueError, u'Invalid value for {}.type: `{}`'.format(name, self.type)

        template_path = 'templates/html/{}_{}.html'.format(name.lower(), self.type)
        html = render_template(template_path, {
            'self': self,
            'custom_choices': self.custom_choices,
        })

        fragment = Fragment(html)
        fragment.add_css_url(self.runtime.local_resource_url(self.xblock_container,
                                                             'public/css/questionnaire.css'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self.xblock_container,
                                                                    'public/js/questionnaire.js'))
        fragment.initialize_js('QuestionnaireBlock')
        return fragment

    @property
    def custom_choices(self):
        custom_choices = []
        for child in self.get_children_objects():
            if isinstance(child, ChoiceBlock):
                custom_choices.append(child)
        return custom_choices

    def get_tips(self):
        """
        Returns the tips contained in this block
        """
        tips = []
        for child in self.get_children_objects():
            if isinstance(child, TipBlock):
                tips.append(child)
        return tips

    def get_submission_display(self, submission):
        """
        Get the human-readable version of a submission value
        """
        for choice in self.custom_choices:
            if choice.value == submission:
                return choice.content
        return submission
