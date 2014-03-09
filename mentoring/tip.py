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
from .utils import render_template


# Globals ###########################################################

log = logging.getLogger(__name__)


# Functions #########################################################

def commas_to_list(commas_str):
    """
    Converts a comma-separated string to a list
    """
    if commas_str is None:
        return None # Means default value (which can be non-empty)
    elif commas_str == '':
        return [] # Means empty list
    else:
        return commas_str.split(',')



# Classes ###########################################################

class TipBlock(LightChild):
    """
    Each choice can define a tip depending on selection
    """
    content = String(help="Text of the tip to provide if needed", scope=Scope.content, default="")
    display = String(help="List of choices to display the tip for", scope=Scope.content, default=None)
    reject = String(help="List of choices to reject", scope=Scope.content, default=None)

    def render(self, submission):
        """
        Returns a fragment containing the formatted tip
        """
        fragment, named_children = self.get_children_fragment({})
        fragment.add_content(render_template('templates/html/tip.html', {
            'self': self,
            'named_children': named_children,
        }))
        return self.xblock_container.fragment_text_rewriting(fragment)

    def is_completed(self, submissions):
        if not submissions:
            return False

        for submission in submissions:
            if submission in self.reject_with_defaults:
                return False
        return True

    def is_tip_displayed(self, submissions):
        for submission in submissions:
            if submission in self.display_with_defaults:
                return True
        return False

    @property
    def display_with_defaults(self):
        display = commas_to_list(self.display)
        if display is None:
            display = self.reject_with_defaults
        else:
            display += [choice for choice in self.reject_with_defaults
                               if choice not in display]
        return display

    @property
    def reject_with_defaults(self):
        reject = commas_to_list(self.reject)
        return reject or []
