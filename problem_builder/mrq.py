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

from xblock.fields import Boolean, List, Scope, String
from xblock.validation import ValidationMessage
from xblockutils.resources import ResourceLoader

from problem_builder.mixins import (ExpandStaticURLMixin,
                                    StudentViewUserStateMixin)

from .questionnaire import QuestionnaireAbstractBlock
from .sub_api import SubmittingXBlockMixin, sub_api

# Globals ###########################################################

log = logging.getLogger(__name__)


# Make '_' a no-op so we can scrape strings
def _(text):
    return text

# Classes ###########################################################


class MRQBlock(SubmittingXBlockMixin, StudentViewUserStateMixin, QuestionnaireAbstractBlock, ExpandStaticURLMixin):
    """
    An XBlock used to ask multiple-response questions
    """
    CATEGORY = 'pb-mrq'
    STUDIO_LABEL = _("Multiple Response Question")
    USER_STATE_FIELDS = ['student_choices', ]

    student_choices = List(
        # Last submissions by the student
        default=[],
        scope=Scope.user_state
    )
    required_choices = List(
        display_name=_("Required Choices"),
        help=_("Specify the value[s] that students must select for this MRQ to be considered correct."),
        scope=Scope.content,
        list_values_provider=QuestionnaireAbstractBlock.choice_values_provider,
        list_style='set',  # Underered, unique items. Affects the UI editor.
        default=[],
    )
    ignored_choices = List(
        display_name=_("Ignored Choices"),
        help=_(
            "Specify the value[s] that are neither correct nor incorrect. "
            "Any values not listed as required or ignored will be considered wrong."
        ),
        scope=Scope.content,
        list_values_provider=QuestionnaireAbstractBlock.choice_values_provider,
        list_style='set',  # Underered, unique items. Affects the UI editor.
        default=[],
    )
    message = String(
        display_name=_("Message"),
        help=_("General feedback provided when submitting"),
        scope=Scope.content,
        default=""
    )
    hide_results = Boolean(display_name="Hide results", scope=Scope.content, default=False)
    editable_fields = (
        'question', 'required_choices', 'ignored_choices', 'message', 'display_name',
        'show_title', 'weight', 'hide_results',
    )

    def describe_choice_correctness(self, choice_value):
        if choice_value in self.required_choices:
            return self._("Required")
        elif choice_value in self.ignored_choices:
            return self._("Ignored")
        return self._("Not Acceptable")

    def get_results(self, previous_result):
        """
        Get the results a student has already submitted.
        """
        result = self.calculate_results(previous_result['submissions'])
        result['completed'] = True
        return result

    def get_last_result(self):
        if self.student_choices:
            return self.get_results({'submissions': self.student_choices})
        else:
            return {}

    def submit(self, submissions):
        log.debug('Received MRQ submissions: "%s"', submissions)

        result = self.calculate_results(submissions)
        self.student_choices = submissions

        log.debug('MRQ submissions result: %s', result)
        return result

    def calculate_results(self, submissions):
        score = 0
        results = []
        tips = None

        if not self.hide_results:
            tips = self.get_tips()

        for choice in self.custom_choices:
            choice_completed = True
            choice_tips_html = []
            choice_selected = choice.value in submissions

            if choice.value in self.required_choices:
                if not choice_selected:
                    choice_completed = False
            elif choice_selected and choice.value not in self.ignored_choices:
                choice_completed = False

            if choice_completed:
                score += 1

            choice_result = {
                'value': choice.value,
                'selected': choice_selected,
                'content': choice.content
            }
            # Only include tips/results in returned response if we want to display them
            if not self.hide_results:
                # choice_tips_html list is being set only when 'self.hide_results' is False, to optimize,
                # execute the loop only when 'self.hide_results' is set to False
                for tip in tips:
                    if choice.value in tip.values:
                        choice_tips_html.append(tip.render('mentoring_view').content)
                        break

                loader = ResourceLoader(__name__)
                choice_result['completed'] = choice_completed
                choice_result['tips'] = loader.render_django_template('templates/html/tip_choice_group.html', {
                    'tips_html': choice_tips_html,
                })

            results.append(choice_result)

        status = 'incorrect' if score <= 0 else 'correct' if score >= len(results) else 'partial'

        if sub_api:
            # Send the answer as a concatenated list to the submissions API
            answer = [choice['content'] for choice in results if choice['selected']]
            sub_api.create_submission(self.student_item_key, ', '.join(answer))

        return {
            'submissions': submissions,
            'status': status,
            'choices': results,
            'message': self.message_formatted,
            'weight': self.weight,
            'score': (float(score) / len(results)) if results else 0,
        }

    def validate_field_data(self, validation, data):
        """
        Validate this block's field data.
        """
        super().validate_field_data(validation, data)

        def add_error(msg):
            validation.add(ValidationMessage(ValidationMessage.ERROR, msg))

        def choice_name(choice_value):
            for choice in self.human_readable_choices:
                if choice["value"] == choice_value:
                    return choice["display_name"]
            return choice_value

        all_values = set(self.all_choice_values)
        required = set(data.required_choices)
        ignored = set(data.ignored_choices)

        if len(required) < len(data.required_choices):
            add_error(self._("Duplicate required choices set"))
        if len(ignored) < len(data.ignored_choices):
            add_error(self._("Duplicate ignored choices set"))
        for val in required.intersection(ignored):
            add_error(self._("A choice is listed as both required and ignored: {}").format(choice_name(val)))
        for val in (required - all_values):
            add_error(self._("A choice value listed as required does not exist: {}").format(choice_name(val)))
        for val in (ignored - all_values):
            add_error(self._("A choice value listed as ignored does not exist: {}").format(choice_name(val)))

    def student_view_data(self, context=None):
        """
        Returns a JSON representation of the student_view of this XBlock,
        retrievable from the Course Block API.
        """
        return {
            'id': self.name,
            'block_id': str(self.scope_ids.usage_id),
            'display_name': self.display_name,
            'title': self.display_name,
            'type': self.CATEGORY,
            'weight': self.weight,
            'question': self.expand_static_url(self.question),
            'message': self.message,
            'choices': [
                {'value': choice['value'], 'content': self.expand_static_url(choice['display_name'])}
                for choice in self.human_readable_choices
            ],
            'hide_results': self.hide_results,
            'tips': [tip.student_view_data() for tip in
                     self.get_tips()] if not self.hide_results else [],
        }
