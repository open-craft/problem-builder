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


# Make '_' a no-op so we can scrape strings
def _(text):
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
        scope=Scope.content,
        default=""
    )
    color_codes = Dict(
        display_name=_("Color Coding"),
        help=_(
            "You can optionally set a color for each expected value. Example: {example_here}"
        ).format(example_here='{ "1": "red", "2": "yellow", 3: "green", 4: "lightskyblue" }')
    )

    editable_fields = ('display_name', 'mentoring_ids', 'color_codes')

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
                    mcq_submission_key = dict(
                        student_id=self.runtime.anonymous_student_id,
                        course_id=unicode(child_id.course_key),
                        item_id=unicode(child_id),
                        item_type=child_id.block_type,
                    )
                    try:
                        value = sub_api.get_submissions(mcq_submission_key, limit=1)[0]["answer"]
                    except IndexError:  # (sub_api.SubmissionNotFoundError, IndexError)
                        value = None
                    block['mcqs'].append({
                        "display_name": mcq_block.question,
                        "value": value,
                        "color": self.color_codes.get(value),
                    })
            blocks.append(block)

        return loader.render_template('templates/html/dashboard.html', {
            'blocks': blocks,
            'display_name': self.display_name,
        })

    def fallback_view(self, view_name, context=None):
        context = context or {}
        context['self'] = self

        if not self.mentoring_ids:
            return Fragment(u"<h1>{}</h1><p>{}</p>".format(self.display_name, _("Not configured.")))

        fragment = Fragment(self.generate_content())
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/dashboard.css'))
        return fragment