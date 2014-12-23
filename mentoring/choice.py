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

from .light_children import LightChild, Scope, String
from .utils import loader, ContextConstants


# Globals ###########################################################

log = logging.getLogger(__name__)


# Classes ###########################################################

class ChoiceBlock(LightChild):
    """
    Custom choice of an answer for a MCQ/MRQ
    """
    value = String(help="Value of the choice when selected", scope=Scope.content, default="")
    content = String(help="Human-readable version of the choice value", scope=Scope.content, default="")
    has_children = True

    def render(self):
        # return self.content
        """
        Returns a fragment containing the formatted tip
        """
        fragment, named_children = self.get_children_fragment({ContextConstants.AS_TEMPLATE: False})
        fragment.add_content(loader.render_template('templates/html/choice.html', {
            'self': self,
            'named_children': named_children,
        }))
        return self.xblock_container.fragment_text_rewriting(fragment)
