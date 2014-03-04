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
import logging

from xblock.fields import Scope

from .light_children import LightChild, String
from .utils import load_resource, render_template


# Globals ###########################################################

log = logging.getLogger(__name__)


# Classes ###########################################################

class MentoringTableBlock(LightChild):
    """
    Table-type display of information from mentoring blocks

    Used to present summary of information entered by the students in mentoring blocks.
    Supports different types of formatting through the `type` parameter.
    """
    type = String(help="Variant of the table to display", scope=Scope.content, default='')
    has_children = True

    def student_view(self, context):
        fragment, columns_frags = self.get_children_fragment(context,
                                                             view_name='mentoring_table_view')
        f, header_frags = self.get_children_fragment(context, view_name='mentoring_table_header_view')

        bg_image_url = self.runtime.local_resource_url(self.xblock_container,
                                                       'public/img/{}-bg.png'.format(self.type))

        # Load an optional description for the background image, for accessibility
        try:
            bg_image_description = load_resource('static/text/table-{}.txt'.format(self.type))
        except IOError as e:
            if e.errno == errno.ENOENT:
                bg_image_description = ''
            else:
                raise

        fragment.add_content(render_template('templates/html/mentoring-table.html', {
            'self': self,
            'columns_frags': columns_frags,
            'header_frags': header_frags,
            'bg_image_url': bg_image_url,
            'bg_image_description': bg_image_description,
        }))
        fragment.add_css_url(self.runtime.local_resource_url(self.xblock_container,
                                                             'public/css/mentoring-table.css'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self.xblock_container,
                                                                    'public/js/vendor/jquery.shorten.js'))
        fragment.add_javascript_url(self.runtime.local_resource_url(self.xblock_container,
                                                                    'public/js/mentoring-table.js'))
        fragment.initialize_js('MentoringTableBlock')

        return fragment

    def mentoring_view(self, context):
        # Allow to render within mentoring blocks, or outside
        return self.student_view(context)


class MentoringTableColumnBlock(LightChild):
    """
    Individual column of a mentoring table
    """
    header = String(help="Header of the column", scope=Scope.content, default=None)
    has_children = True

    def mentoring_table_view(self, context):
        """
        The content of the column
        """
        fragment, named_children = self.get_children_fragment(context,
                                              view_name='mentoring_table_view',
                                              not_instance_of=MentoringTableColumnHeaderBlock)
        fragment.add_content(render_template('templates/html/mentoring-table-column.html', {
            'self': self,
            'named_children': named_children,
        }))
        return fragment

    def mentoring_table_header_view(self, context):
        """
        The content of the column's header
        """
        fragment, named_children = self.get_children_fragment(context,
                                              view_name='mentoring_table_header_view',
                                              instance_of=MentoringTableColumnHeaderBlock)
        fragment.add_content(render_template('templates/html/mentoring-table-header.html', {
            'self': self,
            'named_children': named_children,
        }))
        return fragment


class MentoringTableColumnHeaderBlock(LightChild):
    """
    Header content for a given column
    """
    content = String(help="Body of the header", scope=Scope.content, default='')
    
    def mentoring_table_header_view(self, context):
        fragment = super(MentoringTableColumnHeaderBlock, self).children_view(context)
        fragment.add_content(unicode(self.content))
        return fragment

