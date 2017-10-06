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

from xblock.fields import Scope, String
from xblock.validation import ValidationMessage
from xblockutils.resources import ResourceLoader

from .mixins import StudentViewUserStateMixin
from .questionnaire import QuestionnaireAbstractBlock
from .sub_api import SubmittingXBlockMixin


# Globals ###########################################################
log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)


# Make '_' a no-op so we can scrape strings
def _(text):
    return text


# Classes ###########################################################
class SwipeBlock(SubmittingXBlockMixin, StudentViewUserStateMixin, QuestionnaireAbstractBlock):
    """
    An XBlock used to ask binary-choice questions with a swiping interface
    """
    CATEGORY = 'pb-swipe'
    STUDIO_LABEL = _(u"Swipeable Binary Choice Question")
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

    correct_choice = String(
        display_name=_("Correct Choice"),
        help=_("Specify the value that students may select for this question to be considered correct."),
        scope=Scope.content,
        values_provider=QuestionnaireAbstractBlock.choice_values_provider,
    )
    img_url = String(
        display_name=_("Image"),
        help=_(
            "Specify the URL of an image associated with this question."
        ),
        scope=Scope.content,
        default=""
    )
    editable_fields = QuestionnaireAbstractBlock.editable_fields + ('message', 'correct_choice', 'img_url',)

    def calculate_results(self, submission):
        correct = self.correct_choice == submission
        return {
            'submission': submission,
            'message': self.message_formatted,
            'status': 'correct' if correct else 'incorrect',
            'weight': self.weight,
            'score': 1 if correct else 0,
        }

    def get_results(self, previous_result):
        return self.calculate_results(previous_result['submission'])

    def get_last_result(self):
        return self.get_results({'submission': self.student_choice}) if self.student_choice else {}

    def submit(self, submission):
        log.debug(u'Received Swipe submission: "%s"', submission)
        result = self.calculate_results(submission['value'])
        self.student_choice = submission['value']
        log.debug(u'Swipe submission result: %s', result)
        return result

    def validate_field_data(self, validation, data):
        """
        Validate this block's field data.
        """
        super(SwipeBlock, self).validate_field_data(validation, data)

        def add_error(msg):
            validation.add(ValidationMessage(ValidationMessage.ERROR, msg))

        if len(self.all_choice_values) == 0:
            # Let's not set an error until at least one choice is added
            return

        if len(self.all_choice_values) != 2:
            add_error(
                self._(u"You must have exactly two choices.")
            )
        if not data.correct_choice:
            add_error(
                self._(u"You must indicate the correct answer, or the student will always get this question wrong.")
            )

    def student_view_data(self, context=None):
        """
        Returns a JSON representation of the student_view of this XBlock,
        retrievable from the Course Block API.
        """
        return {
            'id': self.name,
            'block_id': unicode(self.scope_ids.usage_id),
            'display_name': self.display_name_with_default,
            'type': self.CATEGORY,
            'question': self.question,
            'message': self.message,
            'img_url': self.expand_static_url(self.img_url),
            'choices': [
                {'value': choice['value'], 'content': choice['display_name']}
                for choice in self.human_readable_choices
            ],
            'weight': self.weight,
            'tips': [tip.student_view_data() for tip in self.get_tips()],
        }

    def expand_static_url(self, url):
        """
        This is required to make URLs like '/static/dnd-test-image.png' work (note: that is the
        only portable URL format for static files that works across export/import and reruns).
        This method is unfortunately a bit hackish since XBlock does not provide a low-level API
        for this.
        """
        if hasattr(self.runtime, 'replace_urls'):
            url = self.runtime.replace_urls('"{}"'.format(url))[1:-1]
        elif hasattr(self.runtime, 'course_id'):
            # edX Studio uses a different runtime for 'studio_view' than 'student_view',
            # and the 'studio_view' runtime doesn't provide the replace_urls API.
            try:
                from static_replace import replace_static_urls  # pylint: disable=import-error
                url = replace_static_urls('"{}"'.format(url), None, course_id=self.runtime.course_id)[1:-1]
            except ImportError:
                pass
        return url

    @property
    def expanded_img_url(self):
        return self.expand_static_url(self.img_url)
