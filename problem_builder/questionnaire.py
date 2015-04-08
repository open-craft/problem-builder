# -*- coding: utf-8 -*-
#
# Copyright (c) 2014-2015 Harvard, edX & OpenCraft
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

from django.utils.safestring import mark_safe
import logging
from lxml import etree
from xblock.core import XBlock
from xblock.fields import Scope, String, Float, List, UNIQUE_ID
from xblock.fragment import Fragment
from xblock.validation import ValidationMessage
from xblockutils.helpers import child_isinstance
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin, StudioContainerXBlockMixin

from .choice import ChoiceBlock
from .mentoring import MentoringBlock
from .step import StepMixin
from .tip import TipBlock

# Globals ###########################################################

loader = ResourceLoader(__name__)


# Make '_' a no-op so we can scrape strings
def _(text):
    return text

# Classes ###########################################################


@XBlock.needs("i18n")
class QuestionnaireAbstractBlock(StudioEditableXBlockMixin, StudioContainerXBlockMixin, StepMixin, XBlock):
    """
    An abstract class used for MCQ/MRQ blocks

    Must be a child of a MentoringBlock. Allow to display a tip/advice depending on the
    values entered by the student, and supports multiple types of multiple-choice
    set, with preset choices and author-defined values.
    """
    name = String(
        # This doesn't need to be a field but is kept for backwards compatibility with v1 student data
        display_name=_("Question ID (name)"),
        help=_("The ID of this question (required). Should be unique within this mentoring component."),
        default=UNIQUE_ID,
        scope=Scope.settings,  # Must be scope.settings, or the unique ID will change every time this block is edited
    )
    question = String(
        display_name=_("Question"),
        help=_("Question to ask the student"),
        scope=Scope.content,
        default=""
    )
    message = String(
        display_name=_("Message"),
        help=_("General feedback provided when submiting"),
        scope=Scope.content,
        default=""
    )
    weight = Float(
        display_name=_("Weight"),
        help=_("Defines the maximum total grade of this question."),
        default=1,
        scope=Scope.content,
        enforce_type=True
    )
    editable_fields = ('question', 'message', 'weight', 'display_name', 'show_title')
    has_children = True

    def _(self, text):
        """ translate text """
        return self.runtime.service(self, "i18n").ugettext(text)

    @property
    def html_id(self):
        """
        A short, simple ID string used to uniquely identify this question.

        This is only used by templates for matching <input> and <label> elements.
        """
        return unicode(id(self))  # Unique as long as all choices are loaded at once

    def student_view(self, context=None):
        name = getattr(self, "unmixed_class", self.__class__).__name__

        template_path = 'templates/html/{}.html'.format(name.lower())

        context = context or {}
        context['self'] = self
        context['custom_choices'] = self.custom_choices
        context['hide_header'] = context.get('hide_header', False) or not self.show_title

        fragment = Fragment(loader.render_template(template_path, context))
        # If we use local_resource_url(self, ...) the runtime may insert many identical copies
        # of questionnaire.[css/js] into the DOM. So we use the mentoring block here if possible
        block_with_resources = self.get_parent()
        if not isinstance(block_with_resources, MentoringBlock):
            block_with_resources = self
        fragment.add_css_url(self.runtime.local_resource_url(block_with_resources, 'public/css/questionnaire.css'))
        fragment.add_javascript_url(self.runtime.local_resource_url(block_with_resources, 'public/js/questionnaire.js'))
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

    @property
    def human_readable_choices(self):
        return [{"display_name": mark_safe(c.content), "value": c.value} for c in self.custom_choices]

    @staticmethod
    def choice_values_provider(question):
        """
        Get a list a {"display_name": "Choice Description", "value": value}
        objects for use with studio_view editor.
        """
        return question.human_readable_choices

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

    def validate_field_data(self, validation, data):
        """
        Validate this block's field data. Instead of checking fields like self.name, check the
        fields set on data, e.g. data.name. This allows the same validation method to be re-used
        for the studio editor. Any errors found should be added to "validation".

        This method should not return any value or raise any exceptions.
        All of this XBlock's fields should be found in "data", even if they aren't being changed
        or aren't even set (i.e. are defaults).
        """
        super(QuestionnaireAbstractBlock, self).validate_field_data(validation, data)

        def add_error(msg):
            validation.add(ValidationMessage(ValidationMessage.ERROR, msg))
        if not data.name:
            add_error(self._(u"A unique Question ID is required."))
        elif ' ' in data.name:
            add_error(self._(u"Question ID should not contain spaces."))

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
            add_error(self._(u"Some choice values are not unique."))
        # Validate the tips:
        values_with_tips = set()
        for tip in self.get_tips():
            values = set(tip.values)
            if values & values_with_tips:
                add_error(self._(u"Multiple tips configured for the same choice."))
                break
            values_with_tips.update(values)
        return validation
