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

from .common import BlockWithContent
from xblock.fields import Scope, String

# Functions #########################################################

def commas_to_set(commas_str):
    """
    Converts a comma-separated string to a set
    """
    if not commas_str:
        return set()
    else:
        return set(commas_str.split(','))

# Classes ###########################################################


class TipBlock(BlockWithContent):
    """
    Each choice can define a tip depending on selection
    """
    TEMPLATE = 'templates/html/tip.html'

    content = String(help="Text of the tip to provide if needed", scope=Scope.content, default="")
    display = String(help="List of choices to display the tip for", scope=Scope.content, default=None)
    reject = String(help="List of choices to reject", scope=Scope.content, default=None)
    require = String(help="List of choices to require", scope=Scope.content, default=None)
    width = String(help="Width of the tip popup", scope=Scope.content, default='')
    height = String(help="Height of the tip popup", scope=Scope.content, default='')

    @property
    def display_with_defaults(self):
        display = commas_to_set(self.display)
        return display | self.reject_with_defaults | self.require_with_defaults

    @property
    def reject_with_defaults(self):
        return commas_to_set(self.reject)

    @property
    def require_with_defaults(self):
        return commas_to_set(self.require)
