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
from xblockutils.studio_editable import StudioEditableXBlockMixin


# Make '_' a no-op so we can scrape strings
def _(text):
    return text

# Classes ###########################################################


@XBlock.needs("i18n")
class MentoringMessageBlock(XBlock, StudioEditableXBlockMixin):
    """
    A message which can be conditionally displayed at the mentoring block level,
    for example upon completion of the block
    """
    content = String(
        display_name=_("Message"),
        help=_("Message to display upon completion"),
        scope=Scope.content,
        default="",
        multiline_editor="html",
        resettable_editor=False,
    )
    type = String(
        help=_("Type of message"),
        scope=Scope.content,
        default="completed",
        values=(
            {"display_name": "Completed", "value": "completed"},
            {"display_name": "Incompleted", "value": "incomplete"},
            {"display_name": "Reached max. # of attemps", "value": "max_attempts_reached"},
        ),
    )
    editable_fields = ("content", )

    def _(self, text):
        """ translate text """
        return self.runtime.service(self, "i18n").ugettext(text)

    def fallback_view(self, view_name, context):
        html = u'<div class="message {msg_type}">{content}</div>'.format(msg_type=self.type, content=self.content)
        return Fragment(html)

    @property
    def studio_display_name(self):
        if self.type == 'max_attempts_reached':
            max_attempts = self.get_parent().max_attempts
            return self._(u"Message when student reaches max. # of attempts ({limit})").format(
                limit=self._(u"unlimited") if max_attempts == 0 else max_attempts
            )
        if self.type == 'completed':
            return self._(u"Message shown when complete")
        if self.type == 'incomplete':
            return self._(u"Message shown when incomplete")
        return u"INVALID MESSAGE"

    def __getattribute__(self, name):
        """ Provide a read-only display name without adding a display_name field to the class. """
        if name == "display_name":
            return self.studio_display_name
        return super(MentoringMessageBlock, self).__getattribute__(name)

    @classmethod
    def get_template(cls, template_id):
        """
        Used to interact with Studio's create_xblock method to instantiate pre-defined templates.
        """
        return {'data': {'type': template_id, 'content': "Message goes here."}}

    @classmethod
    def parse_xml(cls, node, runtime, keys, id_generator):
        """
        Construct this XBlock from the given XML node.
        """
        block = runtime.construct_xblock_from_class(cls, keys)
        block.content = unicode(node.text or u"")
        block.type = node.attrib['type']
        for child in node:
            block.content += etree.tostring(child, encoding='unicode')

        return block
