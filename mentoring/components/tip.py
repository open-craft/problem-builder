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

from django.utils.html import strip_tags
from lxml import etree

from xblock.core import XBlock
from xblock.fields import Scope, String, List
from xblock.fragment import Fragment
from xblock.validation import ValidationMessage
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin

# Classes ###########################################################


class TipBlock(StudioEditableXBlockMixin, XBlock):
    """
    Each choice can define a tip depending on selection
    """
    content = String(help="Text of the tip to provide if needed", scope=Scope.content, default="")
    values = List(
        display_name="For Choices",
        help="List of choices for which to display this tip",
        scope=Scope.content,
        default=[],
        list_values_provider=lambda self: self.get_parent().human_readable_choices,
        list_style='set',  # Underered, unique items. Affects the UI editor.
    )
    width = String(help="Width of the tip popup", scope=Scope.content, default='')
    height = String(help="Height of the tip popup", scope=Scope.content, default='')
    editable_fields = ('values', 'content', 'width', 'height')

    @property
    def studio_display_name(self):
        values_list = []
        for entry in self.get_parent().human_readable_choices:
            if entry["value"] in self.values:
                display_name = strip_tags(entry["display_name"])  # Studio studio_view can't handle html in display_name
                if len(display_name) > 20:
                    display_name = display_name[:20] + u'…'
                values_list.append(display_name)
        return u"Tip for {}".format(u", ".join(values_list))

    def __getattribute__(self, name):
        """ Provide a read-only display name without adding a display_name field to the class. """
        if name == "display_name":
            return self.studio_display_name
        return super(TipBlock, self).__getattribute__(name)

    def fallback_view(self, view_name, context):
        html = ResourceLoader(__name__).render_template("templates/html/tip.html", {
            'content': self.content,
            'width': self.width,
            'height': self.height,
        })
        return Fragment(html)

    def clean_studio_edits(self, data):
        """
        Clean up the edits during studio_view save
        """
        if "values" in data:
            data["values"] = list([unicode(v) for v in set(data["values"])])

    def validate_field_data(self, validation, data):
        """
        Validate this block's field data.
        """
        super(TipBlock, self).validate_field_data(validation, data)

        def add_error(msg):
            validation.add(ValidationMessage(ValidationMessage.ERROR, msg))

        try:
            valid_values = set(self.get_parent().all_choice_values)
        except Exception:
            pass
        else:
            for val in set(data.values) - valid_values:
                add_error(u"A choice value listed for this tip does not exist: {}".format(val))

    @classmethod
    def parse_xml(cls, node, runtime, keys, id_generator):
        """
        Construct this XBlock from the given XML node.
        """
        block = runtime.construct_xblock_from_class(cls, keys)

        block.values = [unicode(val).strip() for val in node.get('values', '').split(',')]
        block.width = node.get('width', '')
        block.height = node.get('height', '')

        block.content = unicode(node.text or u"")
        for child in node:
            block.content += etree.tostring(child, encoding='unicode')

        return block
