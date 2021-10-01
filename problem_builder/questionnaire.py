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

import uuid

import pkg_resources
from django import utils
from django.utils.safestring import mark_safe
from lazy import lazy
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.fields import Scope, String
from xblock.validation import ValidationMessage
from xblockutils.helpers import child_isinstance
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import (StudioContainerXBlockMixin,
                                         StudioEditableXBlockMixin,
                                         XBlockWithPreviewMixin)

from .choice import ChoiceBlock
from .message import MentoringMessageBlock
from .mixins import QuestionMixin, XBlockWithTranslationServiceMixin
from .tip import TipBlock
from .utils import I18NService

# Globals ###########################################################

loader = ResourceLoader(__name__)


# Make '_' a no-op so we can scrape strings
def _(text):
    return text

# Classes ###########################################################


@XBlock.needs("i18n")
class QuestionnaireAbstractBlock(
    StudioEditableXBlockMixin, StudioContainerXBlockMixin, QuestionMixin, XBlock, XBlockWithPreviewMixin,
    XBlockWithTranslationServiceMixin, I18NService
):
    """
    An abstract class used for MCQ/MRQ blocks

    Must be a child of a MentoringBlock. Allow to display a tip/advice depending on the
    values entered by the student, and supports multiple types of multiple-choice
    set, with preset choices and author-defined values.
    """
    question = String(
        display_name=_("Question"),
        help=_("Question to ask the student"),
        scope=Scope.content,
        default="",
        multiline_editor=True,
    )

    editable_fields = ('question', 'weight', 'display_name', 'show_title')
    has_children = True
    answerable = True

    @lazy
    def html_id(self):
        """
        A short, simple ID string used to uniquely identify this question.

        This is only used by templates for matching <input> and <label> elements.
        """
        return uuid.uuid4().hex[:20]

    @staticmethod
    def resource_string(path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    def get_translation_content(self):
        lang = utils.translation.to_locale(utils.translation.get_language())
        try:
            return self.resource_string(f'public/js/translations/{lang}/textjs.js')
        except OSError:
            return self.resource_string('public/js/translations/en/textjs.js')

    def student_view(self, context=None):
        name = getattr(self, "unmixed_class", self.__class__).__name__

        template_path = f'templates/html/{name.lower()}.html'

        context = context.copy() if context else {}
        context['self'] = self
        context['custom_choices'] = self.custom_choices
        context['hide_header'] = context.get('hide_header', False) or not self.show_title

        fragment = Fragment(loader.render_django_template(template_path, context, i18n_service=self.i18n_service))
        # If we use local_resource_url(self, ...) the runtime may insert many identical copies
        # of questionnaire.[css/js] into the DOM. So we use the mentoring block here if possible.
        block_with_resources = self.get_parent()
        from .mentoring import MentoringBlock

        # We use an inline import here to avoid a circular dependency with the .mentoring module.
        if not isinstance(block_with_resources, MentoringBlock):
            block_with_resources = self
        fragment.add_css_url(self.runtime.local_resource_url(block_with_resources, 'public/css/questionnaire.css'))
        fragment.add_javascript_url(self.runtime.local_resource_url(block_with_resources, 'public/js/questionnaire.js'))
        fragment.add_javascript(self.get_translation_content())
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

    def get_author_edit_view_fragment(self, context):
        fragment = super().author_edit_view(context)
        return fragment

    def author_edit_view(self, context):
        """
        Add some HTML to the author view that allows authors to add choices and tips.
        """
        from .mentoring import MentoringWithExplicitStepsBlock

        fragment = self.get_author_edit_view_fragment(context)

        # * Step Builder units can show review components in the Review Step.
        show_review = isinstance(
            self.get_parent().get_parent() if self.get_parent() else None,
            MentoringWithExplicitStepsBlock
        )
        fragment.add_content(loader.render_django_template('templates/html/questionnaire_add_buttons.html', {
            'show_review': show_review
        }))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/problem-builder.css'))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/questionnaire-edit.css'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/util.js'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/mentoring_edit.js'))
        fragment.initialize_js('MentoringEditComponents')
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
        super().validate_field_data(validation, data)

        def add_error(msg):
            validation.add(ValidationMessage(ValidationMessage.ERROR, msg))
        if not data.name:
            add_error(self._("A unique Question ID is required."))
        elif ' ' in data.name:
            add_error(self._("Question ID should not contain spaces."))

    def validate(self):
        """
        Validates the state of this XBlock.
        """
        validation = super().validate()

        def add_error(msg):
            validation.add(ValidationMessage(ValidationMessage.ERROR, msg))

        # Validate the choice values:
        all_choice_values = self.all_choice_values
        all_choice_values_set = set(all_choice_values)
        if len(all_choice_values) != len(all_choice_values_set):
            add_error(self._("Some choice values are not unique."))
        # Validate the tips:
        values_with_tips = set()
        for tip in self.get_tips():
            values = set(tip.values)
            if values & values_with_tips:
                add_error(self._("Multiple tips configured for the same choice."))
                break
            values_with_tips.update(values)
        return validation

    def get_review_tip(self):
        """ Get the text to show on the assessment review when the student gets this question wrong """
        for child_id in self.children:
            if child_isinstance(self, child_id, MentoringMessageBlock):
                child = self.runtime.get_block(child_id)
                if child.type == "on-assessment-review-question":
                    return child.content

    @property
    def message_formatted(self):
        """ Get the feedback message HTML, if any, formatted by the runtime """
        if self.message:
            # For any HTML that we aren't 'rendering' through an XBlock view such as
            # student_view the runtime may need to rewrite URLs
            # e.g. converting '/static/x.png' to '/c4x/.../x.png'
            format_html = getattr(self.runtime, 'replace_urls', lambda html: html)
            return format_html(self.message)
        return ""
