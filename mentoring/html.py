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

import logging

from lxml import etree

from xblock.fragment import Fragment

from .light_children import LightChild, Scope, String


# Globals ###########################################################

log = logging.getLogger(__name__)


# Classes ###########################################################

class HTMLBlock(LightChild):
    """
    A simplistic replacement for the HTML XModule, as a light XBlock child
    """
    content = String(help="HTML content", scope=Scope.content, default="")

    @classmethod
    def init_block_from_node(cls, block, node, attr):
        block.light_children = []

        node.tag = 'div'
        block.content = unicode(etree.tostring(node))
        node.tag = 'html'

        return block

    def student_view(self, context=None):
        as_template = context.get('as_template', True) if context is not None else True
        if as_template:
            return Fragment(u"<script type='text/template' id='{}'>\n{}\n</script>".format(
                'light-child-template',
                self.content
            ))

        # bug? got AssertionError if I don't use unicode here. (assert isinstance(content, unicode))
        # Although it is set when constructed?
        return Fragment(unicode(self.content))

    def mentoring_view(self, context=None):
        return self.student_view(context)

    def mentoring_table_view(self, context=None):
        return self.student_view(context)
