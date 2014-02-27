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
        
        # TODO-LIGHT-CHILDREN: get real value from `node` (lxml)
        block.content = '<div>Placeholder HTML content</div>'

        return block

    def mentoring_view(self, context=None):
        return Fragment(self.content)
