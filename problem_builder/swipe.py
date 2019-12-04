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
from xblock.core import XBlock
from xblock.fields import Boolean, Scope, String
from xblock.fragment import Fragment
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import (StudioEditableXBlockMixin,
                                         XBlockWithPreviewMixin)

from .mixins import QuestionMixin, StudentViewUserStateMixin

# Globals ###########################################################

log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)


# Make '_' a no-op so we can scrape strings
def _(text):
    return text


# Classes ###########################################################

@XBlock.needs("i18n")
class SwipeBlock(
    QuestionMixin, StudioEditableXBlockMixin, StudentViewUserStateMixin, XBlockWithPreviewMixin, XBlock,
):
    """
    An XBlock used to ask binary-choice questions with a swiping interface
    """
    CATEGORY = 'pb-swipe'
    STUDIO_LABEL = _(u"Swipeable Binary Choice Question")
    USER_STATE_FIELDS = ['student_choice']

    text = String(
        display_name=_("Text"),
        help=_("Text to display on this card. The student must determine if this statement is true or false."),
        scope=Scope.content,
        default="",
        multiline_editor=True,
    )

    img_url = String(
        display_name=_("Image"),
        help=_("Specify the URL of an image associated with this question."),
        scope=Scope.content,
        default=""
    )

    correct = Boolean(
        display_name=_("Correct Choice"),
        help=_("Specifies whether the card is correct."),
        scope=Scope.content,
        default=False,
    )

    feedback_correct = String(
        display_name=_("Correct Answer Feedback"),
        help=_("Feedback to display when student answers correctly."),
        scope=Scope.content,
    )

    feedback_incorrect = String(
        display_name=_("Incorrect Answer Feedback"),
        help=_("Feedback to display when student answers incorrectly."),
        scope=Scope.content,
    )

    student_choice = Boolean(
        scope=Scope.user_state,
        help=_("Last input submitted by the student.")
    )

    editable_fields = ('display_name', 'text', 'img_url', 'correct', 'feedback_correct', 'feedback_incorrect')

    def calculate_results(self, submission):
        correct = submission == self.correct
        return {
            'submission': submission,
            'status': 'correct' if correct else 'incorrect',
            'score': 1 if correct else 0,
            'feedback': self.feedback_correct if correct else self.feedback_incorrect,
        }

    def get_results(self, previous_result):
        return self.calculate_results(previous_result['submission'])

    def get_last_result(self):
        return self.get_results({'submission': self.student_choice}) if self.student_choice else {}

    def submit(self, submission):
        log.debug(u'Received Swipe submission: "%s"', submission)
        # We expect to receive a boolean indicating the swipe the student made (left -> false, right -> true)
        self.student_choice = submission['value']
        result = self.calculate_results(self.student_choice)
        log.debug(u'Swipe submission result: %s', result)
        return result

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
            'text': self.text,
            'img_url': self.expand_static_url(self.img_url),
            'correct': self.correct,
            'feedback': {
                'correct': self.feedback_correct,
                'incorrect': self.feedback_incorrect,
            },
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

    def mentoring_view(self, context=None):
        """ Render the swipe image, text & whether it's correct within a mentoring block question. """
        return Fragment(
            (
                u'<img src="{img_url}" style="max-width: 100%;" />'
                u'<p class="swipe-text">"{text}"</p>'
            ).format(
                img_url=self.expand_static_url(self.img_url),
                text=self.text,
            )
        )

    def student_view(self, context=None):
        """ Normal view of this XBlock, identical to mentoring_view """
        return self.mentoring_view(context)
