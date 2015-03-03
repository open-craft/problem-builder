# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Harvard
#
# Authors:
#          Xavier Antoviaque <xavier@antoviaque.org>
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

import errno


from xblock.core import XBlock
from xblock.exceptions import NoSuchViewError
from xblock.fields import Scope, String
from xblock.fragment import Fragment

from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin, StudioContainerXBlockMixin

# Globals ###########################################################

loader = ResourceLoader(__name__)

# Classes ###########################################################


class MentoringTableBlock(StudioEditableXBlockMixin, StudioContainerXBlockMixin, XBlock):
    """
    Table-type display of information from mentoring blocks

    Used to present summary of information entered by the students in mentoring blocks.
    Supports different types of formatting through the `type` parameter.
    """
    display_name = String(
        display_name="Display name",
        help="Title of the table",
        default="Answers Table",
        scope=Scope.settings
    )
    type = String(
        display_name="Special Mode",
        help="Variant of the table that will display a specific background image.",
        scope=Scope.content,
        default='',
        values=[
            {"display_name": "Normal", "value": ""},
            {"display_name": "Immunity Map Assumptions", "value": "immunity-map-assumptions"},
            {"display_name": "Immunity Map", "value": "immunity-map"},
        ],
    )
    editable_fields = ("type", )
    has_children = True

    def student_view(self, context):
        context = context or {}
        fragment = Fragment()
        header_values = []
        content_values = []
        for child_id in self.children:
            child = self.runtime.get_block(child_id)
            # Child should be an instance of MentoringTableColumn
            header_values.append(child.header)
            child_frag = child.render('mentoring_view', context)
            content_values.append(child_frag.content)
            fragment.add_frag_resources(child_frag)
        context['header_values'] = header_values if any(header_values) else None
        context['content_values'] = content_values

        if self.type:
            # Load an optional background image:
            context['bg_image_url'] = self.runtime.local_resource_url(self, 'public/img/{}-bg.png'.format(self.type))
            # Load an optional description for the background image, for accessibility
            try:
                context['bg_image_description'] = loader.load_unicode('static/text/table-{}.txt'.format(self.type))
            except IOError as e:
                if e.errno == errno.ENOENT:
                    pass
                else:
                    raise

        fragment.add_content(loader.render_template('templates/html/mentoring-table.html', context))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/mentoring-table.css'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/vendor/jquery-shorten.js'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/mentoring-table.js'))
        fragment.initialize_js('MentoringTableBlock')

        return fragment

    def mentoring_view(self, context):
        # Allow to render within mentoring blocks, or outside
        return self.student_view(context)

    def author_edit_view(self, context):
        """
        Add some HTML to the author view that allows authors to add choices and tips.
        """
        fragment = super(MentoringTableBlock, self).author_edit_view(context)
        fragment.add_content(loader.render_template('templates/html/mentoring-table-add-button.html', {}))
        # Share styles with the questionnaire edit CSS:
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/questionnaire-edit.css'))
        return fragment


class MentoringTableColumn(StudioEditableXBlockMixin, StudioContainerXBlockMixin, XBlock):
    """
    A column in a mentoring table. Has a header and can contain HTML and AnswerRecapBlocks.
    """
    display_name = String(display_name="Display Name", default="Column")
    header = String(
        display_name="Header",
        help="Header of this column",
        default="",
        scope=Scope.content,
        multiline_editor="html",
    )
    editable_fields = ("header", )
    has_children = True

    def fallback_view(self, view_name, context):
        context = context or {}
        fragment = Fragment()
        for child_id in self.children:
            child = self.runtime.get_block(child_id)
            if child.scope_ids.block_type == "html":
                # HTML block current doesn't support "mentoring_view" and if "student_view" is used, it gets wrapped
                # with HTML we don't want. So just grab its HTML directly.
                child_frag = Fragment(child.data)
            else:
                child_frag = child.render(view_name, context)
            fragment.add_content(child_frag.content)
            fragment.add_frag_resources(child_frag)
        return fragment

    def author_preview_view(self, context):
        return self.fallback_view('mentoring_view', context)

    def author_edit_view(self, context):
        """
        Add some HTML to the author view that allows authors to add choices and tips.
        """
        fragment = super(MentoringTableColumn, self).author_edit_view(context)
        fragment.content = u"<div style=\"font-weight: bold;\">{}</div>".format(self.header) + fragment.content
        fragment.add_content(loader.render_template('templates/html/mentoring-column-add-button.html', {}))
        # Share styles with the questionnaire edit CSS:
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/questionnaire-edit.css'))
        return fragment
