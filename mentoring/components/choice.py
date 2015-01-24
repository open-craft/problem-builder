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

from xblock.core import XBlock
from xblock.fields import Scope, String
from xblock.fragment import Fragment
from xblockutils.resources import ResourceLoader

# Classes ###########################################################


class ChoiceBlock(XBlock):
    """
    Custom choice of an answer for a MCQ/MRQ
    """
    value = String(help="Value of the choice when selected", scope=Scope.content, default="")
    content = String(help="Human-readable version of the choice value", scope=Scope.content, default="")

    has_children = True

    def render(self):
        """
        Returns a fragment containing the formatted choice
        """
        fragment = Fragment()
        child_content = u""
        for child_id in self.children:
            child = self.runtime.get_block(child_id)
            child_fragment = child.render('mentoring_view', {})
            fragment.add_frag_resources(child_fragment)
            child_content += child_fragment.content
        fragment.add_content(ResourceLoader(__name__).render_template('templates/html/choice.html', {
            'self': self,
            'child_content': child_content,
        }))
        return fragment  # TODO: fragment_text_rewriting
