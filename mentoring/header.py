# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Harvard
#
# Authors:
#          Xavier Antoviaque <xavier@antoviaque.org>
#          David Gabor Bodor <david.gabor.bodor@gmail.com>
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

import logging
from lxml import etree
from xblock.fragment import Fragment
from .light_children import LightChild, Scope, String

log = logging.getLogger(__name__)


class SharedHeaderBlock(LightChild):
    """
    A shared header block shown under the title.
    """

    content = String(help="HTML content of the header", scope=Scope.content, default="")

    @classmethod
    def init_block_from_node(cls, block, node, attr):
        block.light_children = []

        node.tag = 'div'
        block.content = unicode(etree.tostring(node))
        node.tag = 'shared-header'

        return block

    def student_view(self, context=None):
        return Fragment(u"<script type='text/template' id='light-child-template'>\n{}\n</script>".format(
            self.content
        ))

    def mentoring_view(self, context=None):
        return self.student_view(context)

    def mentoring_table_view(self, context=None):
        return self.student_view(context)
