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

from lazy import lazy
from xblock.fields import String, Boolean, Scope
from xblockutils.helpers import child_isinstance


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


class StepParentMixin(object):
    """
    An XBlock mixin for a parent block containing Step children
    """

    @property
    def steps(self):
        """
        Get the usage_ids of all of this XBlock's children that are "Steps"
        """
        return [_normalize_id(child_id) for child_id in self.children if child_isinstance(self, child_id, StepMixin)]


class StepMixin(object):
    """
    An XBlock mixin for a child block that is a "Step".

    A step is a question that the user can answer (as opposed to a read-only child).
    """
    has_author_view = True

    # Fields:
    display_name = String(
        display_name=_("Question title"),
        help=_('Leave blank to use the default ("Question 1", "Question 2", etc.)'),
        default="",  # Blank will use 'Question x' - see display_name_with_default
        scope=Scope.content
    )
    show_title = Boolean(
        display_name=_("Show title"),
        help=_("Display the title?"),
        default=True,
        scope=Scope.content
    )

    @lazy
    def step_number(self):
        return list(self.get_parent().steps).index(_normalize_id(self.scope_ids.usage_id)) + 1

    @lazy
    def lonely_step(self):
        if _normalize_id(self.scope_ids.usage_id) not in self.get_parent().steps:
            raise ValueError("Step's parent should contain Step", self, self.get_parent().steps)
        return len(self.get_parent().steps) == 1

    @property
    def display_name_with_default(self):
        """ Get the title/display_name of this question. """
        if self.display_name:
            return self.display_name
        if not self.lonely_step:
            return self._(u"Question {number}").format(number=self.step_number)
        return self._(u"Question")

    def author_view(self, context):
        context = context or {}
        context['hide_header'] = True
        return self.mentoring_view(context)

    def author_preview_view(self, context):
        context = context or {}
        context['hide_header'] = True
        return self.student_view(context)

    def assessment_step_view(self, context=None):
        """
        assessment_step_view is the same as mentoring_view, except its DIV will have a different
        class (.xblock-v1-assessment_step_view) that we use for assessments to hide all the
        steps with CSS and to detect which children of mentoring are "Steps" and which are just
        decorative elements/instructions.
        """
        return self.mentoring_view(context)
