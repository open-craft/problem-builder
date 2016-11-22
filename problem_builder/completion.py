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

from xblock.core import XBlock
from xblock.fields import Scope, String, Boolean
from xblock.fragment import Fragment
from xblockutils.studio_editable import StudioEditableXBlockMixin
from xblockutils.resources import ResourceLoader

from .mixins import QuestionMixin, XBlockWithTranslationServiceMixin
from .sub_api import sub_api, SubmittingXBlockMixin


# Globals ###########################################################

log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)


# Make '_' a no-op so we can scrape strings
def _(text):
    return text


# Classes ###########################################################

@XBlock.needs('i18n')
class CompletionBlock(
        SubmittingXBlockMixin, QuestionMixin, StudioEditableXBlockMixin, XBlockWithTranslationServiceMixin, XBlock
):
    """
    An XBlock used by students to indicate that they completed a given task.
    The student's answer is always considered "correct".
    """
    CATEGORY = 'pb-completion'
    STUDIO_LABEL = _(u'Completion')
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

    student_value = Boolean(
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

        html = loader.render_template('templates/html/completion.html', context)

        fragment = Fragment(html)
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/completion.js'))
        fragment.initialize_js('CompletionBlock')
        return fragment

    student_view = mentoring_view
    preview_view = mentoring_view

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
        log.debug(u'Received Completion submission: "%s"', value)
        self.student_value = value
        if sub_api:
            # Also send to the submissions API:
            sub_api.create_submission(self.student_item_key, value)
        result = self.get_last_result()
        log.debug(u'Completion submission result: %s', result)
        return result
