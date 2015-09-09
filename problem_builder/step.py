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

from lazy.lazy import lazy

from xblock.core import XBlock
from xblock.fields import String, Boolean, Scope
from xblock.fragment import Fragment
from xblockutils.helpers import child_isinstance
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import (
    NestedXBlockSpec, StudioEditableXBlockMixin, StudioContainerWithNestedXBlocksMixin, XBlockWithPreviewMixin
)

from problem_builder.answer import AnswerBlock, AnswerRecapBlock
from problem_builder.mcq import MCQBlock, RatingBlock
from problem_builder.mixins import EnumerableChildMixin
from problem_builder.mrq import MRQBlock
from problem_builder.table import MentoringTableBlock


loader = ResourceLoader(__name__)


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


class HtmlBlockShim(object):
    CATEGORY = 'html'
    STUDIO_LABEL = _(u"HTML")


@XBlock.needs('i18n')
class MentoringStepBlock(
        StudioEditableXBlockMixin, StudioContainerWithNestedXBlocksMixin, XBlockWithPreviewMixin,
        EnumerableChildMixin, XBlock
):
    """
    An XBlock for a step.
    """
    CAPTION = _(u"Step")
    STUDIO_LABEL = _(u"Mentoring Step")
    CATEGORY = 'pb-mentoring-step'

    # Fields:
    display_name = String(
        display_name=_("Step Title"),
        help=_('Leave blank to use sequential numbering'),
        default="",
        scope=Scope.content
    )

    editable_fields = ('display_name', 'show_title',)

    @lazy
    def siblings(self):
        return self.get_parent().steps

    @property
    def allowed_nested_blocks(self):
        """
        Returns a list of allowed nested XBlocks. Each item can be either
        * An XBlock class
        * A NestedXBlockSpec

        If XBlock class is used it is assumed that this XBlock is enabled and allows multiple instances.
        NestedXBlockSpec allows explicitly setting disabled/enabled state, disabled reason (if any) and single/multiple
        instances
        """
        return [
            NestedXBlockSpec(AnswerBlock, boilerplate='studio_default'),
            MCQBlock, RatingBlock, MRQBlock, HtmlBlockShim,
            AnswerRecapBlock, MentoringTableBlock,
        ]

    @property
    def steps(self):
        """ Get the usage_ids of all of this XBlock's children that are "Questions" """
        from mixins import QuestionMixin
        return [
            _normalize_id(child_id) for child_id in self.children if child_isinstance(self, child_id, QuestionMixin)
        ]

    def author_edit_view(self, context):
        """
        Add some HTML to the author view that allows authors to add child blocks.
        """
        local_context = dict(context)
        local_context['wrap_children'] = {
            'head': u'<div class="mentoring">',
            'tail': u'</div>'
        }
        fragment = super(MentoringStepBlock, self).author_edit_view(local_context)
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/problem-builder.css'))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/problem-builder-edit.css'))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/problem-builder-tinymce-content.css'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/util.js'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/step_edit.js'))
        fragment.initialize_js('StepEdit')
        return fragment

    def student_view(self, context=None):
        """ Student View """
        return self._render_view(context, 'student_view')

    def mentoring_view(self, context=None):
        """ Mentoring View """
        return self._render_view(context, 'mentoring_view')

    def _render_view(self, context, view):
        """ Actually renders a view """
        fragment = Fragment()
        child_contents = []

        for child_id in self.children:
            child = self.runtime.get_block(child_id)
            if child is None:  # child should not be None but it can happen due to bugs or permission issues
                child_contents.append(u"<p>[{}]</p>".format(self._(u"Error: Unable to load child component.")))
            else:
                child_fragment = self._render_child_fragment(child, context, view)

                fragment.add_frag_resources(child_fragment)
                child_contents.append(child_fragment.content)

        fragment.add_content(loader.render_template('templates/html/step.html', {
            'self': self,
            'title': self.display_name,
            'show_title': self.show_title,
            'child_contents': child_contents,
        }))

        return fragment
