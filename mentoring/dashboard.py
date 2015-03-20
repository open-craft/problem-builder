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
from lazy import lazy

from .sub_api import sub_api
from xblock.core import XBlock
from xblock.fields import Scope, String
from xblock.fragment import Fragment
from xblock.validation import ValidationMessage
from xblockutils.studio_editable import StudioEditableXBlockMixin


# Globals ###########################################################

log = logging.getLogger(__name__)


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
    mcq_id = String(
        display_name=_("MCQ ID"),
        help=_("THe url_name of an MCQ to use as a proof of concept for using the submissions API"),
        scope=Scope.content,
        default=""
    )

    editable_fields = ('display_name', 'mcq_id', )

    def fallback_view(self, view_name, context=None):
        context = context or {}
        context['self'] = self

        if self.mcq_id:
            item_usage_key = self.scope_ids.usage_id.course_key.make_usage_key('pb-mcq', self.mcq_id)
            item_key = dict(
                student_id=self.runtime.anonymous_student_id,
                course_id=unicode(item_usage_key.course_key),
                item_id=unicode(item_usage_key),
                item_type=item_usage_key.block_type,
            )
            try:
                submission = sub_api.get_submissions(item_key, limit=1)[0]
            except (sub_api.SubmissionNotFoundError, IndexError):
                message = "(No answer submitted yet)"
            else:
                message = "Answer is: {}.".format(submission["answer"])
        else:
            message = "(Not configured)"

        fragment = Fragment(u"<h1>Dashboard</h1><p>{}</p>".format(message))
        return fragment
