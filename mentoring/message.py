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


# Classes ###########################################################

class MentoringMessageBlock(LightChild):
    """
    A message which can be conditionally displayed at the mentoring block level,
    for example upon completion of the block
    """
    content = String(help="Message to display upon completion", scope=Scope.content, default="")
    type = String(help="Type of message", scope=Scope.content, default="completed")
    has_children = True

    def mentoring_view(self, context=None):
        fragment, named_children = self.get_children_fragment(context, view_name='mentoring_view')
        fragment.add_content(render_template('templates/html/message.html', {
            'self': self,
            'named_children': named_children,
        }))
        return fragment
