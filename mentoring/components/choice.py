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
from xblock.validation import ValidationMessage
from xblockutils.studio_editable import StudioEditableXBlockMixin

# Classes ###########################################################


class ChoiceBlock(StudioEditableXBlockMixin, XBlock):
    """
    Custom choice of an answer for a MCQ/MRQ
    """
    value = String(
        display_name="Value",
        help="Value of the choice when selected. Should be unique.",
        scope=Scope.content,
        default="",
    )
    content = String(
        display_name="Choice Text",
        help="Human-readable version of the choice value",
        scope=Scope.content,
        default="",
    )
    editable_fields = ('value', 'content')

    @property
    def display_name(self):
        try:
            status = self.get_parent().describe_choice_correctness(self.value)
        except Exception:
            status = u"Out of Context"  # Parent block should implement describe_choice_correctness()
        return u"Choice ({}) ({})".format(self.value, status)

    def fallback_view(self, view_name, context):
        return Fragment(u'<span class="choice-text">{}</span>'.format(self.content))

    def validate_field_data(self, validation, data):
        """
        Validate this block's field data.
        """
        super(ChoiceBlock, self).validate_field_data(validation, data)

        def add_error(msg):
            validation.add(ValidationMessage(ValidationMessage.ERROR, msg))

        if not data.value.strip():
            add_error(u"No value set. This choice will not work correctly.")
        if not data.content.strip():
            add_error(u"No choice text set yet.")

    @classmethod
    def parse_xml(cls, node, runtime, keys, id_generator):
        """
        Construct this XBlock from the given XML node.
        """
        block = runtime.construct_xblock_from_class(cls, keys)
        for field_name in cls.editable_fields:
            if field_name in node.attrib:
                setattr(block, field_name, node.attrib[field_name])

        # HTML content:
        block.content = unicode(node.text or u"")
        for child in node:
            block.content += etree.tostring(child, encoding='unicode')

        return block
