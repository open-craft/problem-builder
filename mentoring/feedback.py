# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Harvard
#
# Authors:
#          Alan Boudreault <alan@alanb.ca>
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

class FeedbackBlock(LightChild):
    """
    Represent a feedback block. Currently only used to set the width/heigth style but could be
    useful to set a static header/body etc.
    """
    width = String(help="Width of the feedback popup", scope=Scope.content, default='')
    height = String(help="Height of the feedback popup", scope=Scope.content, default='')

    def render(self):
        """
        Returns a fragment containing the formatted feedback
        """
        fragment, named_children = self.get_children_fragment({})
        fragment.add_content(render_template('templates/html/feedback.html', {
            'self': self,
            'named_children': named_children,
        }))
        return self.xblock_container.fragment_text_rewriting(fragment)
