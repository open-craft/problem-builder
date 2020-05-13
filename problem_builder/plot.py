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

import six
from lazy.lazy import lazy
from xblock.core import XBlock
from xblock.fields import Scope, String
from xblock.fragment import Fragment
from xblock.validation import ValidationMessage
from xblockutils.helpers import child_isinstance
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import (StudioContainerWithNestedXBlocksMixin,
                                         StudioEditableXBlockMixin,
                                         XBlockWithPreviewMixin)

from .mixins import StudentViewUserStateMixin
from .sub_api import sub_api

loader = ResourceLoader(__name__)

log = logging.getLogger(__name__)


# Make '_' a no-op so we can scrape strings
def _(text):
    return text


def _normalize_id(key):
    """
    Helper method to normalize a key to avoid issues where some keys have version/branch and others don't.
    e.g. self.scope_ids.usage_id != self.runtime.get_block(self.scope_ids.usage_id).scope_ids.usage_id
    """
    if hasattr(key, "for_branch"):
        key = key.for_branch(None)
    if hasattr(key, "for_version"):
        key = key.for_version(None)
    return key


@XBlock.needs('i18n')
@XBlock.wants('user')
class PlotBlock(
    StudioEditableXBlockMixin, StudioContainerWithNestedXBlocksMixin, XBlockWithPreviewMixin, XBlock,
    StudentViewUserStateMixin,
):
    """
    XBlock that displays plot that summarizes answers to scale and/or rating questions.
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
            'where "claim" is arbitrary text that represents a claim, '
            'and "q1" and "q2" are IDs of scale or rating questions. '
        ),
        default="",
        multiline_editor=True,
        resettable_editor=False
    )

    editable_fields = (
        'display_name', 'plot_label', 'point_color_default', 'point_color_average',
        'q1_label', 'q2_label', 'q3_label', 'q4_label', 'claims'
    )

    @lazy
    def course_key_str(self):
        location = _normalize_id(self.location)
        return six.text_type(location.course_key)

    @property
    def default_claims(self):
        return self._get_claims(self._get_default_response)

    @property
    def average_claims(self):
        return self._get_claims(self._get_average_response)

    def _get_claims(self, response_function):
        if not self.claims:
            return []

        mentoring_block = self.get_parent().get_parent()
        question_ids, questions = mentoring_block.question_ids, mentoring_block.questions
        claims = []
        for line in self.claims.split('\n'):
            claim, q1, q2 = line.split(', ')
            r1, r2 = None, None
            for question_id, question in zip(question_ids, questions):
                if question.url_name == q1:
                    r1 = response_function(question, question_id)
                if question.url_name == q2:
                    r2 = response_function(question, question_id)
                if r1 is not None and r2 is not None:
                    break
            claims.append([claim, r1, r2])

        return claims

    def _get_default_response(self, question, question_id):
        # 1. Obtain block_type for question
        question_type = question.scope_ids.block_type
        # 2. Obtain latest submission for question
        student_dict = {
            'student_id': self.runtime.anonymous_student_id,
            'course_id': self.course_key_str,
            'item_id': question_id,
            'item_type': question_type,
        }
        submissions = sub_api.get_submissions(student_dict, limit=1)
        # 3. Extract response from latest submission for question
        answer_cache = {}
        for submission in submissions:
            answer = self._get_answer(question, submission, answer_cache)
            return int(answer)

    def _get_average_response(self, question, question_id):
        # 1. Obtain block_type for question
        question_type = question.scope_ids.block_type
        # 2. Obtain latest submissions for question
        submissions = sub_api.get_all_submissions(self.course_key_str, question_id, question_type)
        # 3. Extract responses from latest submissions for question and sum them up
        answer_cache = {}
        response_total = 0
        num_submissions = 0  # Can't use len(submissions) because submissions is a generator
        for submission in submissions:
            answer = self._get_answer(question, submission, answer_cache)
            response_total += int(answer)
            num_submissions += 1
        # 4. Calculate average response for question
        if num_submissions:
            return response_total / float(num_submissions)

    def _get_answer(self, block, submission, answer_cache):
        """
        Return answer associated with `submission` to `block`.

        `answer_cache` is a dict that is reset for each block.
        """
        answer = submission['answer']
        # Convert from answer ID to answer label
        if answer not in answer_cache:
            answer_cache[answer] = block.get_submission_display(answer)
        return answer_cache[answer]

    def default_claims_json(self):
        return json.dumps(self.default_claims)

    def average_claims_json(self):
        return json.dumps(self.average_claims)

    def build_user_state_data(self, context=None):
        user_state_data = super(PlotBlock, self).build_user_state_data()
        user_state_data['default_claims'] = self.default_claims
        user_state_data['average_claims'] = self.average_claims
        return user_state_data

    @XBlock.json_handler
    def get_data(self, data, suffix):
        return {
            'default_claims': self.default_claims,
            'average_claims': self.average_claims,
        }

    @property
    def allowed_nested_blocks(self):
        """
        Returns a list of allowed nested XBlocks. Each item can be either

        * An XBlock class
        * A NestedXBlockSpec

        If XBlock class is used it is assumed that this XBlock is enabled and allows multiple instances.
        NestedXBlockSpec allows explicitly setting disabled/enabled state,
        disabled reason (if any) and single/multiple instances.
        """
        return [PlotOverlayBlock]

    @lazy
    def overlay_ids(self):
        """
        Get the usage_ids of all of this XBlock's children that are overlays.
        """
        return [
            _normalize_id(child_id) for child_id in self.children if
            child_isinstance(self, child_id, PlotOverlayBlock)
        ]

    @lazy
    def overlays(self):
        """
        Get the overlay children of this block.
        """
        return [self.runtime.get_block(overlay_id) for overlay_id in self.overlay_ids]

    @lazy
    def overlay_data(self):
        if not self.claims:
            return []

        overlay_data = []
        claims = self.claims.split('\n')
        for index, overlay in enumerate(self.overlays):
            claims_json = []
            if overlay.claim_data:
                claim_data = overlay.claim_data.split('\n')
                for claim, data in zip(claims, claim_data):
                    claim = claim.split(', ')[0]
                    r1, r2 = data.split(', ')
                    claims_json.append([claim, int(r1), int(r2)])
            claims_json = json.dumps(claims_json)
            overlay_data.append({
                'plot_label': overlay.plot_label,
                'point_color': overlay.point_color,
                'description': overlay.description,
                'citation': overlay.citation,
                'claims_json': claims_json,
                'position': index,
            })
        return overlay_data

    @lazy
    def claims_display(self):
        if not self.claims:
            return []

        claims = []
        for claim in self.claims.split('\n'):
            claim, q1, q2 = claim.split(', ')
            claims.append([claim, q1, q2])
        return claims

    def author_preview_view(self, context):
        context['self'] = self
        fragment = Fragment()
        fragment.add_content(loader.render_django_template('templates/html/plot_preview.html', context))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/plot-preview.css'))
        if self.overlay_ids:
            fragment.add_content(
                u"<p>{}</p>".format(
                    _(u"In addition to the default and average overlays the plot includes the following overlays:")
                ))
            for overlay in self.overlays:
                overlay_fragment = self._render_child_fragment(overlay, context, view='mentoring_view')
                fragment.add_frag_resources(overlay_fragment)
                fragment.add_content(overlay_fragment.content)
        return fragment

    def mentoring_view(self, context):
        return self.student_view(context)

    def student_view(self, context=None):
        """ Student View """
        context = context.copy() if context else {}
        context['hide_header'] = True
        context['self'] = self
        fragment = Fragment()
        fragment.add_content(loader.render_django_template('templates/html/plot.html', context))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/plot.css'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/vendor/d3.min.js'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/plot.js'))
        fragment.initialize_js('PlotBlock')
        return fragment

    def student_view_data(self, context=None):
        """
        Returns a JSON representation of the student_view of this XBlock,
        retrievable from the Course XBlock API.
        """
        return {
            'display_name': self.display_name,
            'type': self.CATEGORY,
            'title': self.display_name,
            'q1_label': self.q1_label,
            'q2_label': self.q2_label,
            'q3_label': self.q3_label,
            'q4_label': self.q4_label,
            'point_color_default': self.point_color_default,
            'plot_label': self.plot_label,
            'point_color_average': self.point_color_average,
            'overlay_data': self.overlay_data,
            'hide_header': True,
            'claims': self.claims,
        }

    def author_edit_view(self, context):
        """
        Add some HTML to the author view that allows authors to add child blocks.
        """
        fragment = super(PlotBlock, self).author_edit_view(context)
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/problem-builder-edit.css'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/util.js'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/container_edit.js'))
        fragment.initialize_js('ProblemBuilderContainerEdit')
        return fragment


@XBlock.needs('i18n')
class PlotOverlayBlock(StudioEditableXBlockMixin, XBlockWithPreviewMixin, XBlock):
    """
    XBlock that represents a user-defined overlay for a plot block.
    """

    CATEGORY = 'sb-plot-overlay'
    STUDIO_LABEL = _(u"Plot Overlay")

    # Settings
    display_name = String(
        display_name=_("Overlay title"),
        default="Overlay",
        scope=Scope.content
    )

    plot_label = String(
        display_name=_("Plot label"),
        help=_("Label for button that allows to toggle visibility of this overlay"),
        default="",
        scope=Scope.content
    )

    point_color = String(
        display_name=_("Point color"),
        help=_("Point color to use for this overlay"),
        default="",
        scope=Scope.content
    )

    description = String(
        display_name=_("Description"),
        help=_("Description of this overlay (optional)"),
        default="",
        scope=Scope.content
    )

    citation = String(
        display_name=_("Citation"),
        help=_("Source of data belonging to this overlay (optional)"),
        default="",
        scope=Scope.content
    )

    claim_data = String(
        display_name=_("Claim data"),
        help=_(
            'Claim data to include in this overlay. '
            'Each line defines a tuple of the form "q1, q2", '
            'where "q1" is the value associated with the first scale or rating question, '
            'and "q2" is the value associated with the second scale or rating question. '
            'Note that data will be associated with claims in the order that they are defined in the parent plot.'
        ),
        default="",
        multiline_editor=True,
        resettable_editor=False
    )

    editable_fields = (
        "plot_label", "point_color", "description", "citation", "claim_data"
    )

    def validate_field_data(self, validation, data):
        """
        Validate this block's field data.
        """
        super(PlotOverlayBlock, self).validate_field_data(validation, data)

        def add_error(msg):
            validation.add(ValidationMessage(ValidationMessage.ERROR, msg))

        if not data.plot_label.strip():
            add_error(_(u"No plot label set. Button for toggling visibility of this overlay will not have a label."))
        if not data.point_color.strip():
            add_error(_(u"No point color set. This overlay will not work correctly."))

        # If parent plot is associated with one or more claims, prompt user to add claim data
        parent = self.get_parent()
        if parent.claims.strip() and not data.claim_data.strip():
            add_error(_(u"No claim data provided. This overlay will not work correctly."))

    def author_preview_view(self, context):
        return self.student_view(context)

    def mentoring_view(self, context):
        context = context.copy() if context else {}
        context['hide_header'] = True
        return self.author_preview_view(context)

    def student_view(self, context):
        context['self'] = self
        fragment = Fragment()
        fragment.add_content(loader.render_django_template('templates/html/overlay.html', context))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/overlay.css'))
        return fragment
