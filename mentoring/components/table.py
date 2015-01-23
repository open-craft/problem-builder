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
from xblock.fields import Scope, String
from xblock.fragment import Fragment

from xblockutils.resources import ResourceLoader
loader = ResourceLoader(__name__)

# Globals ###########################################################

loader = ResourceLoader(__name__)

# Classes ###########################################################


class MentoringTableBlock(XBlock):
    """
    Table-type display of information from mentoring blocks

    Used to present summary of information entered by the students in mentoring blocks.
    Supports different types of formatting through the `type` parameter.
    """
    type = String(help="Variant of the table to display", scope=Scope.content, default='')
    has_children = True

    def student_view(self, context):
        fragment = Fragment()
        columns_frags = []
        header_frags = []
        for child_id in self.children:
            child = self.runtime.get_block(child_id)
            column_fragment = child.render('mentoring_table_view', context)
            fragment.add_frag_resources(column_fragment)
            columns_frags.append((child.name, column_fragment))
            header_fragment = child.render('mentoring_table_header_view', context)
            fragment.add_frag_resources(header_fragment)
            header_frags.append((child.name, header_fragment))

        bg_image_url = self.runtime.local_resource_url(self, 'public/img/{}-bg.png'.format(self.type))

        # Load an optional description for the background image, for accessibility
        try:
            bg_image_description = loader.load_unicode('static/text/table-{}.txt'.format(self.type))
        except IOError as e:
            if e.errno == errno.ENOENT:
                bg_image_description = ''
            else:
                raise

        fragment.add_content(loader.render_template('templates/html/mentoring-table.html', {
            'self': self,
            'columns_frags': columns_frags,
            'header_frags': header_frags,
            'bg_image_url': bg_image_url,
            'bg_image_description': bg_image_description,
        }))
        fragment.add_css_url(self.runtime.local_resource_url(self, 'public/css/mentoring-table.css'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/vendor/jquery-shorten.js'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/mentoring-table.js'))
        fragment.initialize_js('MentoringTableBlock')

        return fragment

    def mentoring_view(self, context):
        # Allow to render within mentoring blocks, or outside
        return self.student_view(context)


class MentoringTableColumnBlock(XBlock):
    """
    Individual column of a mentoring table
    """
    header = String(help="Header of the column", scope=Scope.content, default=None)
    has_children = True

    def _render_table_view(self, view_name, id_filter, template, context):
        fragment = Fragment()
        named_children = []
        for child_id in self.children:
            if id_filter(child_id):
                child = self.runtime.get_block(child_id)
                child_frag = child.render(view_name, context)
                fragment.add_frag_resources(child_frag)
                named_children.append((child.name, child_frag))

        fragment.add_content(loader.render_template('templates/html/{}'.format(template), {
            'self': self,
            'named_children': named_children,
        }))
        return fragment

    def mentoring_table_view(self, context):
        """
        The content of the column
        """
        return self._render_table_view(
            view_name='mentoring_table_view',
            id_filter=lambda child_id: not issubclass(self._get_child_class(child_id), MentoringTableColumnHeaderBlock),
            template='mentoring-table-column.html',
            context=context
        )

    def mentoring_table_header_view(self, context):
        """
        The content of the column's header
        """
        return self._render_table_view(
            view_name='mentoring_table_header_view',
            id_filter=lambda child_id: issubclass(self._get_child_class(child_id), MentoringTableColumnHeaderBlock),
            template='mentoring-table-header.html',
            context=context
        )

    def _get_child_class(self, child_id):
        """
        Helper method to get a block type from a usage_id without loading the block.

        Returns the XBlock subclass of the child block.
        """
        type_name = self.runtime.id_reader.get_block_type(self.runtime.id_reader.get_definition_id(child_id))
        return self.runtime.load_block_type(type_name)


class MentoringTableColumnHeaderBlock(XBlock):
    """
    Header content for a given column
    """
    content = String(help="Body of the header", scope=Scope.content, default='')

    def mentoring_table_header_view(self, context):
        return Fragment(unicode(self.content))
