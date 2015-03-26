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
"""
Dashboard: Summarize the results of self-assessments done by a student with Problem Builder MCQ
blocks.

The author of this block specifies a list of Problem Builder blocks containing MCQs. This block
will then display a table summarizing the values that the student chose for each of those MCQs.
"""
# Imports ###########################################################

import json
import logging

from .dashboard_visual import DashboardVisualData
from .mcq import MCQBlock
from .sub_api import sub_api
from xblock.core import XBlock
from xblock.exceptions import XBlockNotFoundError
from xblock.fields import Scope, Dict, List, String
from xblock.fragment import Fragment
from xblock.validation import ValidationMessage
from xblockutils.helpers import child_isinstance
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin


# Globals ###########################################################

log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)


def _(text):
    """ A no-op to mark strings that we need to translate """
    return text

# Classes ###########################################################


@XBlock.needs("i18n")
class DashboardBlock(StudioEditableXBlockMixin, XBlock):
    """
    A block to summarize self-assessment results.
    """
    display_name = String(
        display_name=_("Display Name"),
        help=_("Display name for this module"),
        scope=Scope.settings,
        default=_('Self-Assessment Summary'),
    )
    mentoring_ids = List(
        display_name=_("Mentoring Blocks"),
        help=_(
            "This should be an ordered list of the url_names of each mentoring block whose multiple choice question "
            "values are to be shown on this dashboard. The list should be in JSON format. Example: {example_here}"
        ).format(example_here='["2754b8afc03a439693b9887b6f1d9e36", "215028f7df3d4c68b14fb5fea4da7053"]'),
        scope=Scope.settings,
        default=""
    )
    color_codes = Dict(
        display_name=_("Color Coding"),
        help=_(
            "You can optionally set a color for each expected value. Example: {example_here}"
        ).format(example_here='{ "1": "red", "2": "yellow", 3: "green", 4: "lightskyblue" }'),
        scope=Scope.content,
    )
    visual_rules = String(
        display_name=_("Visual Representation"),
        default="",
        help=_("Optional: Enter the JSON configuration of the visual representation desired (Advanced)."),
        scope=Scope.content,
        multiline_editor=True,
        resettable_editor=False,
    )

    editable_fields = ('display_name', 'mentoring_ids', 'color_codes', 'visual_rules')

    def get_mentoring_blocks(self):
        """
        Generator returning the specified mentoring blocks, in order.

        returns a list. Will insert None for every invalid mentoring block ID.
        """
        for url_name in self.mentoring_ids:
            mentoring_id = self.scope_ids.usage_id.course_key.make_usage_key('problem-builder', url_name)
            try:
                yield self.runtime.get_block(mentoring_id)
            except XBlockNotFoundError:
                yield None

    def _get_submission_key(self, usage_key):
        """
        Given the usage_key of an MCQ block, get the dict key needed to look it up with the
        submissions API.
        """
        return dict(
            student_id=self.runtime.anonymous_student_id,
            course_id=unicode(usage_key.course_key),
            item_id=unicode(usage_key),
            item_type=usage_key.block_type,
        )

    def generate_content(self):
        """
        Create the HTML for this block, by getting the data and inserting it into a template.
        """
        blocks = []
        for mentoring_block in self.get_mentoring_blocks():
            if mentoring_block is None:
                continue
            block = {
                'display_name': mentoring_block.display_name,
                'mcqs': []
            }
            for child_id in mentoring_block.children:
                if child_isinstance(mentoring_block, child_id, MCQBlock):
                    # Get the student's submitted answer to this MCQ from the submissions API:
                    mcq_block = self.runtime.get_block(child_id)
                    mcq_submission_key = self._get_submission_key(child_id)
                    try:
                        value = sub_api.get_submissions(mcq_submission_key, limit=1)[0]["answer"]
                    except IndexError:
                        value = None
                    block['mcqs'].append({
                        "display_name": mcq_block.question,
                        "value": value,
                        "color": self.color_codes.get(value),
                    })
            # If the values are numeric, display an average:
            numeric_values = [float(mcq['value']) for mcq in block['mcqs'] if mcq['value'] and mcq['value'].isnumeric()]
            if numeric_values:
                block['average'] = sum(numeric_values) / len(numeric_values)
                block['has_average'] = True
            blocks.append(block)

        visual_repr = None
        if self.visual_rules:
            try:
                rules_parsed = json.loads(self.visual_rules)
            except ValueError:
                pass  # JSON errors should be shown as part of validation
            else:
                visual_repr = DashboardVisualData(blocks, rules_parsed)

        return loader.render_template('templates/html/dashboard.html', {
            'blocks': blocks,
            'display_name': self.display_name,
            'visual_repr': visual_repr,
        })

    def student_view(self, context=None):  # pylint: disable=unused-argument
        """
        Standard view of this XBlock.
        """
        if not self.mentoring_ids:
            return Fragment(u"<h1>{}</h1><p>{}</p>".format(self.display_name, _("Not configured.")))

        fragment = Fragment(self.generate_content())
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/dashboard.css'))
        return fragment

    def validate_field_data(self, validation, data):
        """
        Validate this block's field data.
        """
        super(DashboardBlock, self).validate_field_data(validation, data)

        def add_error(msg):
            validation.add(ValidationMessage(ValidationMessage.ERROR, msg))

        if data.visual_rules:
            try:
                rules = json.loads(data.visual_rules)
            except ValueError as e:
                add_error(_(u"Visual rules contains an error: {error}").format(error=e))
            else:
                if not isinstance(rules, dict):
                    add_error(_(u"Visual rules should be a JSON dictionary/object: {...}"))
