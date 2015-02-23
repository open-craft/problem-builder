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

from lxml import etree
from xblock.core import XBlock
from xblock.fields import Scope, String, Float, List
from xblock.fragment import Fragment
from xblock.validation import ValidationMessage
from xblockutils.helpers import child_isinstance
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin, StudioContainerXBlockMixin

from .choice import ChoiceBlock
from .step import StepMixin
from .tip import TipBlock

# Globals ###########################################################

loader = ResourceLoader(__name__)

# Classes ###########################################################


class property_with_default(property):
    """
    Decorator for creating a dynamic display_name property that looks like an XBlock field. This
    is needed for Studio container page blocks as studio will try to read
    BlockClass.display_name.default
    """
    default = u"Question"


class QuestionnaireAbstractBlock(StudioEditableXBlockMixin, StudioContainerXBlockMixin, StepMixin, XBlock):
    """
    An abstract class used for MCQ/MRQ blocks

    Must be a child of a MentoringBlock. Allow to display a tip/advice depending on the
    values entered by the student, and supports multiple types of multiple-choice
    set, with preset choices and author-defined values.
    """
    question = String(
        display_name="Question",
        help="Question to ask the student",
        scope=Scope.content,
        default=""
    )
    message = String(
        display_name="Message",
        help="General feedback provided when submiting",
        scope=Scope.content,
        default=""
    )
    weight = Float(
        display_name="Weight",
        help="Defines the maximum total grade of this question.",
        default=1,
        scope=Scope.content,
        enforce_type=True
    )
    editable_fields = ('question', 'message', 'weight')
    has_children = True

    @classmethod
    def parse_xml(cls, node, runtime, keys, id_generator):
        """
        Custom XML parser that can handle list type fields properly,
        as well as the old way of defining 'question' and 'message' field values via tags.
        """
        block = runtime.construct_xblock_from_class(cls, keys)

        # Load XBlock properties from the XML attributes:
        for name, value in node.items():
            field = block.fields[name]
            if isinstance(field, List) and not value.startswith('['):
                # This list attribute is just a string of comma separated strings:
                setattr(block, name, [unicode(val).strip() for val in value.split(',')])
            elif isinstance(field, String):
                setattr(block, name, value)
            else:
                setattr(block, name, field.from_json(value))

        for xml_child in node:
            if xml_child.tag is not etree.Comment:
                block.runtime.add_node_as_child(block, xml_child, id_generator)

        return block

    @property_with_default
    def display_name(self):
        return u"Question {}".format(self.step_number) if not self.lonely_step else u"Question"

    def student_view(self, context=None):
        name = getattr(self, "unmixed_class", self.__class__).__name__

        template_path = 'templates/html/{}.html'.format(name.lower())

        context = context or {}
        context['self'] = self
        context['custom_choices'] = self.custom_choices

        fragment = Fragment(loader.render_template(template_path, context))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/questionnaire.css'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/questionnaire.js'))
        fragment.initialize_js(name)
        return fragment

    def mentoring_view(self, context=None):
        return self.student_view(context)

    @property
    def custom_choices(self):
        custom_choices = []
        for child_id in self.children:
            if child_isinstance(self, child_id, ChoiceBlock):
                custom_choices.append(self.runtime.get_block(child_id))
        return custom_choices

    @property
    def all_choice_values(self):
        return [c.value for c in self.custom_choices]

    def get_tips(self):
        """
        Returns the tips contained in this block
        """
        tips = []
        for child_id in self.children:
            if child_isinstance(self, child_id, TipBlock):
                tips.append(self.runtime.get_block(child_id))
        return tips

    def get_submission_display(self, submission):
        """
        Get the human-readable version of a submission value
        """
        for choice in self.custom_choices:
            if choice.value == submission:
                return choice.content
        return submission

    def author_edit_view(self, context):
        """
        Add some HTML to the author view that allows authors to add choices and tips.
        """
        fragment = super(QuestionnaireAbstractBlock, self).author_edit_view(context)
        fragment.add_content(loader.render_template('templates/html/questionnaire_add_buttons.html', {}))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/questionnaire-edit.css'))
        return fragment

    def validate(self):
        """
        Validates the state of this XBlock.
        """
        validation = super(QuestionnaireAbstractBlock, self).validate()

        def add_error(msg):
            validation.add(ValidationMessage(ValidationMessage.ERROR, msg))

        # Validate the choice values:
        all_choice_values = self.all_choice_values
        all_choice_values_set = set(all_choice_values)
        if len(all_choice_values) != len(all_choice_values_set):
            add_error(u"Some choice values are not unique.")
        # Validate the tips:
        values_with_tips = set()
        for tip in self.get_tips():
            values = set(tip.values)
            for val in (values & values_with_tips):
                add_error(u"Multiple tips for value '{}'".format(val))
            values_with_tips.update(values)
        return validation
