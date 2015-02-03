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

from lxml import etree

from xblock.core import XBlock
from xblock.fields import Scope, String
from xblock.fragment import Fragment

# Classes ###########################################################


class HTMLBlock(XBlock):
    """
    Render content as HTML
    """
    FIXED_CSS_CLASS = "html_child"

    content = String(help="HTML content", scope=Scope.content, default="")
    css_class = String(help="CSS Class[es] applied to wrapper div element", scope=Scope.content, default="")

    @classmethod
    def parse_xml(cls, node, runtime, keys, id_generator):
        """
        Construct this XBlock from the given XML node.
        """
        block = runtime.construct_xblock_from_class(cls, keys)

        if node.get('class'):  # Older API used "class" property, not "css_class"
            node.set('css_class', node.get('css_class', node.get('class')))
            del node.attrib['class']
        block.css_class = node.get('css_class')

        block.content = unicode(node.text or u"")
        for child in node:
            block.content += etree.tostring(child, encoding='unicode')

        return block

    def fallback_view(self, view_name, context=None):
        """ Default view handler """
        css_class = ' '.join(cls for cls in (self.css_class, self.FIXED_CSS_CLASS) if cls)
        html = u'<div class="{classes}">{content}</div>'.format(classes=css_class, content=unicode(self.content))
        return Fragment(html)
