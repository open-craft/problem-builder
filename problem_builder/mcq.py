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

import logging

import six
from xblock.fields import List, Scope, String
from xblock.fragment import Fragment
from xblock.validation import ValidationMessage
from xblockutils.resources import ResourceLoader

from problem_builder.mixins import (ExpandStaticURLMixin,
                                    StudentViewUserStateMixin)

from .questionnaire import QuestionnaireAbstractBlock
from .sub_api import SubmittingXBlockMixin, sub_api

# Globals ###########################################################

log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)


# Make '_' a no-op so we can scrape strings
def _(text):
    return text

# Classes ###########################################################


class MCQBlock(SubmittingXBlockMixin, StudentViewUserStateMixin, QuestionnaireAbstractBlock, ExpandStaticURLMixin):
    """
    An XBlock used to ask multiple-choice questions
    """
    CATEGORY = 'pb-mcq'
    STUDIO_LABEL = _(u"Multiple Choice Question")
    USER_STATE_FIELDS = ['num_attempts', 'student_choice']

    message = String(
        display_name=_("Message"),
        help=_(
            "General feedback provided when submitting. "
            "(This is not shown if there is a more specific feedback tip for the choice selected by the learner.)"
        ),
        scope=Scope.content,
        default=""
    )

    student_choice = String(
        # {Last input submitted by the student
        default="",
        scope=Scope.user_state,
    )

    correct_choices = List(
        display_name=_("Correct Choice[s]"),
        help=_("Specify the value[s] that students may select for this question to be considered correct."),
        scope=Scope.content,
        list_values_provider=QuestionnaireAbstractBlock.choice_values_provider,
        list_style='set',  # Underered, unique items. Affects the UI editor.
    )
    editable_fields = QuestionnaireAbstractBlock.editable_fields + ('message', 'correct_choices',)

    def describe_choice_correctness(self, choice_value):
        if choice_value in self.correct_choices:
            if len(self.correct_choices) == 1:
                # Translators: This is an adjective, describing a choice as correct
                return self._(u"Correct")
            return self._(u"Acceptable")
        else:
            if len(self.correct_choices) == 1:
                return self._(u"Wrong")
            return self._(u"Not Acceptable")

    def calculate_results(self, submission):
        correct = submission in self.correct_choices
        tips_html = []
        for tip in self.get_tips():
            if submission in tip.values:
                tips_html.append(tip.render('mentoring_view').content)

        formatted_tips = None

        if tips_html:
            formatted_tips = loader.render_django_template('templates/html/tip_choice_group.html', {
                'tips_html': tips_html,
            })

        self.student_choice = submission

        if sub_api:
            # Also send to the submissions API:
            sub_api.create_submission(self.student_item_key, submission)

        return {
            'submission': submission,
            'message': self.message_formatted,
            'status': 'correct' if correct else 'incorrect',
            'tips': formatted_tips,
            'weight': self.weight,
            'score': 1 if correct else 0,
        }

    def get_results(self, previous_result):
        return self.calculate_results(previous_result['submission'])

    def get_last_result(self):
        return self.get_results({'submission': self.student_choice}) if self.student_choice else {}

    def submit(self, submission):
        log.debug(u'Received MCQ submission: "%s"', submission)
        result = self.calculate_results(submission['value'])
        self.student_choice = submission['value']
        log.debug(u'MCQ submission result: %s', result)
        return result

    def get_author_edit_view_fragment(self, context):
        """
        The options for the 1-5 values of the Likert scale aren't child blocks but we want to
        show them in the author edit view, for clarity.
        """
        fragment = Fragment(u"<p>{}</p>".format(self.question))
        self.render_children(context, fragment, can_reorder=True, can_add=False)
        return fragment

    def validate_field_data(self, validation, data):
        """
        Validate this block's field data.
        """
        super(MCQBlock, self).validate_field_data(validation, data)

        def add_error(msg):
            validation.add(ValidationMessage(ValidationMessage.ERROR, msg))

        def choice_name(choice_value):
            for choice in self.human_readable_choices:
                if choice["value"] == choice_value:
                    return choice["display_name"]
            return choice_value

        all_values = set(self.all_choice_values)
        correct = set(data.correct_choices)

        if all_values and not correct:
            add_error(
                self._(u"You must indicate the correct answer[s], or the student will always get this question wrong.")
            )
        if len(correct) < len(data.correct_choices):
            add_error(self._(u"Duplicate correct choices set"))
        for val in (correct - all_values):
            add_error(
                self._(u"A choice value listed as correct does not exist: {choice}").format(choice=choice_name(val))
            )

    def student_view_data(self, context=None):
        """
        Returns a JSON representation of the student_view of this XBlock,
        retrievable from the Course Block API.
        """
        return {
            'id': self.name,
            'block_id': six.text_type(self.scope_ids.usage_id),
            'display_name': self.display_name_with_default,
            'type': self.CATEGORY,
            'question': self.expand_static_url(self.question),
            'message': self.message,
            'choices': [
                {'value': choice['value'], 'content': self.expand_static_url(choice['display_name'])}
                for choice in self.human_readable_choices
            ],
            'weight': self.weight,
            'tips': [tip.student_view_data() for tip in self.get_tips()],
        }


class RatingBlock(MCQBlock):
    """
    An XBlock used to rate something on a five-point scale, e.g. Likert Scale
    """
    CATEGORY = 'pb-rating'
    STUDIO_LABEL = _(u"Rating Question")

    low = String(
        display_name=_("Low"),
        help=_("Label for low ratings"),
        scope=Scope.content,
        default=_("Less"),
    )
    high = String(
        display_name=_("High"),
        help=_("Label for high ratings"),
        scope=Scope.content,
        default=_("More"),
    )
    FIXED_VALUES = ["1", "2", "3", "4", "5"]
    correct_choices = List(
        display_name=_("Accepted Choice[s]"),
        help=_("Specify the rating value[s] that students may select for this question to be considered correct."),
        scope=Scope.content,
        default=FIXED_VALUES,
        list_values_provider=QuestionnaireAbstractBlock.choice_values_provider,
        list_style='set',  # Underered, unique items. Affects the UI editor.
    )
    editable_fields = MCQBlock.editable_fields + ('low', 'high')

    @property
    def all_choice_values(self):
        return self.FIXED_VALUES + [c.value for c in self.custom_choices]

    @property
    def human_readable_choices(self):
        display_names = ["1 - {}".format(self.low), "2", "3", "4", "5 - {}".format(self.high)]
        return [
            {"display_name": dn, "value": val} for val, dn in zip(self.FIXED_VALUES, display_names)
        ] + super(RatingBlock, self).human_readable_choices

    def get_author_edit_view_fragment(self, context):
        """
        The options for the 1-5 values of the Likert scale aren't child blocks but we want to
        show them in the author edit view, for clarity.
        """
        fragment = Fragment()
        fragment.add_content(loader.render_django_template('templates/html/ratingblock_edit_preview.html', {
            'question': self.question,
            'low': self.low,
            'high': self.high,
            'accepted_statuses': [None] + [self.describe_choice_correctness(c) for c in "12345"],
        }))
        self.render_children(context, fragment, can_reorder=True, can_add=False)
        return fragment

    @property
    def url_name(self):
        """
        Get the url_name for this block. In Studio/LMS it is provided by a mixin, so we just
        defer to super(). In the workbench or any other platform, we use the name.
        """
        try:
            return super(RatingBlock, self).url_name
        except AttributeError:
            return self.name

    def student_view(self, context):
        fragment = super(RatingBlock, self).student_view(context)
        rendering_for_studio = None
        if context:  # Workbench does not provide context
            rendering_for_studio = context.get('author_edit_view')
        if rendering_for_studio:
            fragment.add_content(loader.render_django_template('templates/html/rating_edit_footer.html', {
                "url_name": self.url_name
            }))
        return fragment
