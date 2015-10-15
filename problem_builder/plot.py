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

import json
import logging

from opaque_keys.edx.keys import CourseKey

from xblock.core import XBlock
from xblock.fields import String, Scope
from xblock.fragment import Fragment
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import (
    StudioEditableXBlockMixin, StudioContainerWithNestedXBlocksMixin, XBlockWithPreviewMixin
)
from .sub_api import sub_api


loader = ResourceLoader(__name__)

log = logging.getLogger(__name__)


# Make '_' a no-op so we can scrape strings
def _(text):
    return text


@XBlock.needs('i18n')
@XBlock.wants('user')
class PlotBlock(StudioEditableXBlockMixin, StudioContainerWithNestedXBlocksMixin, XBlockWithPreviewMixin, XBlock):
    """
    XBlock that displays plot that summarizes answers to scale questions.
    """

    CATEGORY = 'sb-plot'
    STUDIO_LABEL = _(u"Plot")

    # Settings
    display_name = String(
        display_name=_("Plot title"),
        default="Plot",
        scope=Scope.content
    )

    plot_label = String(
        display_name=_("Plot label"),
        help=_("Label for default overlay that shows student's answers to scale questions"),
        default="yours",
        scope=Scope.content
    )

    point_color_default = String(
        display_name=_("Point color (default overlay)"),
        help=_("Point color to use for default overlay"),
        default="green",
        scope=Scope.content
    )

    point_color_average = String(
        display_name=_("Point color (average overlay)"),
        help=_("Point color to use for average overlay"),
        default="blue",
        scope=Scope.content
    )

    q1_label = String(
        display_name=_("Quadrant I"),
        help=_(
            "Label for the first quadrant. "
            "Plot uses counter-clockwise numbering starting in the top right quadrant."
        ),
        default="Q1",
        scope=Scope.content
    )

    q2_label = String(
        display_name=_("Quadrant II"),
        help=_(
            "Label for the second quadrant. "
            "Plot uses counter-clockwise numbering starting in the top right quadrant."
        ),
        default="Q2",
        scope=Scope.content
    )

    q3_label = String(
        display_name=_("Quadrant III"),
        help=_(
            "Label for the third quadrant. "
            "Plot uses counter-clockwise numbering starting in the top right quadrant."
        ),
        default="Q3",
        scope=Scope.content
    )

    q4_label = String(
        display_name=_("Quadrant IV"),
        help=_(
            "Label for the fourth quadrant. "
            "Plot uses counter-clockwise numbering starting in the top right quadrant."
        ),
        default="Q4",
        scope=Scope.content
    )

    claims = String(
        display_name=_("Claims and associated questions"),
        help=_(
            'Claims and questions that should be included in the plot. '
            'Each line defines a triple of the form "claim, q1, q2", '
            'where "claim" is arbitrary text that represents a claim (must be quoted using double-quotes), '
            'and "q1" and "q2" are IDs of scale questions. '
        ),
        default="",
        multiline_editor=True,
        resettable_editor=False
    )

    editable_fields = (
        'display_name', 'plot_label', 'point_color_default', 'point_color_average',
        'q1_label', 'q2_label', 'q3_label', 'q4_label', 'claims'
    )

    @property
    def default_claims(self):
        if not self.claims:
            return []

        course_id = unicode(getattr(self.runtime, 'course_id', 'course_id'))
        course_key = CourseKey.from_string(course_id)
        course_key_str = unicode(course_key)

        user_service = self.runtime.service(self, 'user')
        user = user_service.get_current_user()
        username = user.opt_attrs.get('edx-platform.username')
        anonymous_user_id = user_service.get_anonymous_user_id(username, course_id)

        mentoring_block = self.get_parent().get_parent()
        question_ids, questions = mentoring_block.question_ids, mentoring_block.questions
        claims = []
        for line in self.claims.split('\n'):
            claim, q1, q2 = line.split(', ')
            r1, r2 = None, None
            for question_id, question in zip(question_ids, questions):
                if question.name == q1:
                    r1 = self._default_response(course_key_str, question, question_id, anonymous_user_id)
                if question.name == q2:
                    r2 = self._default_response(course_key_str, question, question_id, anonymous_user_id)
                if r1 is not None and r2 is not None:
                    break
            claims.append([claim, r1, r2])

        return claims

    def _default_response(self, course_key_str, question, question_id, user_id):
        from .tasks import _get_answer  # Import here to avoid circular dependency
        # 1. Obtain block_type for question
        question_type = question.scope_ids.block_type
        # 2. Obtain submissions for question using course_key_str, block_id, block_type, user_id
        student_dict = {
            'student_id': user_id,
            'course_id': course_key_str,
            'item_id': question_id,
            'item_type': question_type,
        }
        submissions = sub_api.get_submissions(student_dict, limit=1)  # Gets latest submission
        # 3. Extract response from latest submission for question
        answer_cache = {}
        for submission in submissions:
            answer = _get_answer(question, submission, answer_cache)
            return int(answer)

    @property
    def average_claims(self):
        if not self.claims:
            return []

        course_id = unicode(getattr(self.runtime, 'course_id', 'course_id'))
        course_key = CourseKey.from_string(course_id)
        course_key_str = unicode(course_key)

        mentoring_block = self.get_parent().get_parent()
        question_ids, questions = mentoring_block.question_ids, mentoring_block.questions
        claims = []
        for line in self.claims.split('\n'):
            claim, q1, q2 = line.split(', ')
            r1, r2 = None, None
            for question_id, question in zip(question_ids, questions):
                if question.name == q1:
                    r1 = self._average_response(course_key_str, question, question_id)
                if question.name == q2:
                    r2 = self._average_response(course_key_str, question, question_id)
                if r1 is not None and r2 is not None:
                    break
            claims.append([claim, r1, r2])

        return claims

    def _average_response(self, course_key_str, question, question_id):
        from .tasks import _get_answer  # Import here to avoid circular dependency
        # 1. Obtain block_type for question
        question_type = question.scope_ids.block_type
        # 2. Obtain submissions for question using course_key_str, block_id, block_type
        submissions = sub_api.get_all_submissions(course_key_str, question_id, question_type)  # Gets latest submissions
        # 3. Extract responses from submissions for question and sum them up
        answer_cache = {}
        response_total = 0
        num_submissions = 0  # Can't use len(submissions) because submissions is a generator
        for submission in submissions:
            answer = _get_answer(question, submission, answer_cache)
            response_total += int(answer)
            num_submissions += 1
        # 4. Calculate average response for question
        if num_submissions:
            return response_total / float(num_submissions)

    def default_claims_json(self):
        return json.dumps(self.default_claims)

    def average_claims_json(self):
        return json.dumps(self.average_claims)

    @XBlock.json_handler
    def get_data(self, data, suffix):
        return {
            'default_claims': self.default_claims,
            'average_claims': self.average_claims,
        }

    def clean_studio_edits(self, data):
        # FIXME: Use this to clean data.claims (remove leading/trailing whitespace, etc.)
        pass

    def validate_field_data(self, validation, data):
        # FIXME: Use this to validate data.claims:
        # - Each line should be of the form "claim, q1, q2" (no quotes)
        # - Entries for "claim", "q1", "q2" must point to existing blocks
        pass

    def author_preview_view(self, context):
        return Fragment(
            u"<p>{}</p>".format(
                _(u"This block displays a plot that summarizes answers to scale questions.")
            )
        )

    def mentoring_view(self, context):
        return self.student_view(context)

    def student_view(self, context=None):
        """ Student View """
        context = context.copy() if context else {}
        context['hide_header'] = True
        context['self'] = self
        fragment = Fragment()
        fragment.add_content(loader.render_template('templates/html/plot.html', context))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/plot.css'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/vendor/underscore-min.js'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/vendor/d3.min.js'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/plot.js'))
        fragment.initialize_js('PlotBlock')
        return fragment
