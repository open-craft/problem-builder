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

from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.fields import UNSET, JSONField, Scope, String
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin

from .mixins import (QuestionMixin, StudentViewUserStateMixin,
                     XBlockWithTranslationServiceMixin)
from .sub_api import SubmittingXBlockMixin, sub_api

# Globals ###########################################################

log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)


# Make '_' a no-op so we can scrape strings
def _(text):
    return text


# Classes ###########################################################


class NullableBoolean(JSONField):
    """
    A field class for representing a boolean which may also be ``null``,
    indicating that a value has not been assigned.

    The value, as loaded or enforced, can be either a Python bool, ``None``,
    a string, or any value that will then be converted to a bool in the
    ``from_json`` method.

    Examples:
1
    ::

        True -> True
        'true' -> True
        'TRUE' -> True
        'any other string' -> False
        [] -> False
        ['123'] -> True
        None - > None

    """
    # We're OK redefining built-in `help`
    def __init__(self, help=None, default=UNSET, scope=Scope.content, display_name=None,
                 **kwargs):  # pylint: disable=redefined-builtin
        super().__init__(
            help,
            default,
            scope,
            display_name,
            values=({'display_name': "True", "value": True},
                    {'display_name': "False", "value": False},
                    {'display_name': "Null", "value": None}),
            **kwargs
        )

    def from_json(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            value = value.decode('ascii', errors='replace')
        if isinstance(value, str):
            return value.lower() == 'true'
        else:
            return bool(value)

    enforce_type = from_json


@XBlock.needs('i18n')
class CompletionBlock(
    SubmittingXBlockMixin, QuestionMixin, StudioEditableXBlockMixin, XBlockWithTranslationServiceMixin,
    StudentViewUserStateMixin, XBlock
):
    """
    An XBlock used by students to indicate that they completed a given task.
    The student's answer is always considered "correct".
    """
    CATEGORY = 'pb-completion'
    STUDIO_LABEL = _('Completion')
    USER_STATE_FIELDS = ['student_value']

    answerable = True

    question = String(
        display_name=_('Question'),
        help=_('Mentions a specific activity and asks the student whether they completed it.'),
        scope=Scope.content,
        default=_(
            'Please indicate whether you attended the In Person Workshop session by (un-)checking the option below.'
        ),
    )

    answer = String(
        display_name=_('Answer'),
        help=_(
            'Represents the answer that the student can (un-)check '
            'to indicate whether they completed the activity that the question mentions.'
        ),
        scope=Scope.content,
        default=_('Yes, I attended the session.'),
    )

    student_value = NullableBoolean(
        help=_("Records student's answer."),
        scope=Scope.user_state,
        default=None,
    )

    editable_fields = ('display_name', 'show_title', 'question', 'answer')

    def mentoring_view(self, context):
        """
        Main view of this block.
        """
        context = context.copy() if context else {}
        context['question'] = self.question
        context['answer'] = self.answer
        context['checked'] = self.student_value if self.student_value is not None else False
        context['title'] = self.display_name_with_default
        context['hide_header'] = context.get('hide_header', False) or not self.show_title

        html = loader.render_django_template('templates/html/completion.html', context)

        fragment = Fragment(html)
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/completion.js'))
        fragment.initialize_js('CompletionBlock')
        return fragment

    student_view = mentoring_view
    preview_view = mentoring_view

    def student_view_data(self, context=None):
        """
        Returns a JSON representation of the student_view of this XBlock,
        retrievable from the Course XBlock API.
        """
        return {
            'id': self.name,
            'block_id': str(self.scope_ids.usage_id),
            'display_name': self.display_name_with_default,
            'type': self.CATEGORY,
            'question': self.question,
            'answer': self.answer,
            'title': self.display_name_with_default,
            'hide_header': not self.show_title,
        }

    def get_last_result(self):
        """ Return the current/last result in the required format """
        if self.student_value is None:
            return {}
        return {
            'submission': self.student_value,
            'status': 'correct',
            'tips': [],
            'weight': self.weight,
            'score': 1,
        }

    def get_results(self):
        """ Alias for get_last_result() """
        return self.get_last_result()

    def submit(self, value):
        """
        Persist answer submitted by student.
        """
        log.debug('Received Completion submission: "%s"', value)
        self.student_value = value
        if sub_api:
            # Also send to the submissions API:
            sub_api.create_submission(self.student_item_key, value)
        result = self.get_last_result()
        log.debug('Completion submission result: %s', result)
        return result
