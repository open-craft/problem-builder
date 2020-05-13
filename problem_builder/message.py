# -*- coding: utf-8 -*-
#
# Copyright (c) 2014-2015 Harvard, edX & OpenCraft
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

import six
# Imports ###########################################################
from lxml import etree
from xblock.core import XBlock
from xblock.fields import Scope, String
from xblock.fragment import Fragment
from xblockutils.studio_editable import StudioEditableXBlockMixin

from problem_builder.mixins import XBlockWithTranslationServiceMixin


# Make '_' a no-op so we can scrape strings
def _(text):
    return text

# Classes ###########################################################


@XBlock.needs("i18n")
class MentoringMessageBlock(XBlock, StudioEditableXBlockMixin, XBlockWithTranslationServiceMixin):
    """
    A message which can be conditionally displayed at the mentoring block level,
    for example upon completion of the block
    """
    MESSAGE_TYPES = {
        "completed": {
            "display_name": _(u"Completed"),
            "studio_label": _(u'Message (Complete)'),
            "long_display_name": _(u"Message shown when complete"),
            "default": _(u"Great job!"),
            "description": _(
                u"This message will be shown when the student achieves a perfect score. "
            ),
        },
        "incomplete": {
            "display_name": _(u"Incomplete"),
            "studio_label": _(u'Message (Incomplete)'),
            "long_display_name": _(u"Message shown when incomplete"),
            "default": _(u"Not quite! You can try again, though."),
            "description": _(
                u"This message will be shown when the student gets at least one question wrong, "
                "but is allowed to try again. "
            ),
        },
        "max_attempts_reached": {
            "display_name": _(u"Reached max. # of attempts"),
            "studio_label": _(u'Message (Max # Attempts)'),
            "long_display_name": _(u"Message shown when student reaches max. # of attempts"),
            "default": _(u"Sorry, you have used up all of your allowed submissions."),
            "description": _(
                u"This message will be shown when the student has used up "
                "all of their allowed attempts without achieving a perfect score. "
            ),
        },
        "on-assessment-review-question": {
            "display_name": _(u"Study tips if this question was wrong"),
            "long_display_name": _(u"Study tips shown if question was answered incorrectly"),
            "default": _(
                u"Review ____."
            ),
            "description": _(
                u"This message will be shown when the student is reviewing "
                "their answers to the assessment, if the student got this specific question "
                "wrong and is allowed to try again."
            ),
        },
    }

    has_author_view = True

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
            {"value": "completed", "display_name": MESSAGE_TYPES["completed"]["display_name"]},
            {"value": "incomplete", "display_name": MESSAGE_TYPES["incomplete"]["display_name"]},
            {"value": "max_attempts_reached", "display_name": MESSAGE_TYPES["max_attempts_reached"]["display_name"]},
            {
                "value": "on-assessment-review-question",
                "display_name": MESSAGE_TYPES["on-assessment-review-question"]["display_name"]
            },
        ),
    )
    editable_fields = ("content", )

    def mentoring_view(self, context=None):
        """ Render this message for use by a mentoring block. """
        html = u'<div class="submission-message {msg_type}">{content}</div>'.format(
            msg_type=self.type,
            content=self.content
        )
        return Fragment(html)

    def student_view(self, context=None):
        """ Normal view of this XBlock, identical to mentoring_view """
        return self.mentoring_view(context)

    def author_view(self, context=None):
        fragment = self.mentoring_view(context)
        fragment.content += u'<div class="submission-message-help"><p>{}</p></div>'.format(self.help_text)
        return fragment

    @property
    def display_name_with_default(self):
        try:
            return self._(self.MESSAGE_TYPES[self.type]["long_display_name"])
        except KeyError:
            return u"INVALID MESSAGE"

    @property
    def help_text(self):
        try:
            return self._(self.MESSAGE_TYPES[self.type]["description"])
        except KeyError:
            return u"This message is not a valid message type!"

    @classmethod
    def get_template(cls, template_id):
        """
        Used to interact with Studio's create_xblock method to instantiate pre-defined templates.
        """
        return {'data': {
            'type': template_id,
            'content': cls.MESSAGE_TYPES[template_id]["default"],
        }}

    @classmethod
    def parse_xml(cls, node, runtime, keys, id_generator):
        """
        Construct this XBlock from the given XML node.
        """
        block = runtime.construct_xblock_from_class(cls, keys)
        block.content = six.text_type(node.text or u"")
        if 'type' in node.attrib:  # 'type' is optional - default is 'completed'
            block.type = node.attrib['type']
        for child in node:
            block.content += etree.tostring(child, encoding='unicode')

        return block


class CompletedMentoringMessageShim:
    CATEGORY = 'pb-message'
    STUDIO_LABEL = _("Message (Complete)")


class IncompleteMentoringMessageShim:
    CATEGORY = 'pb-message'
    STUDIO_LABEL = _("Message (Incomplete)")


def get_message_label(type):
    return MentoringMessageBlock.MESSAGE_TYPES[type]['studio_label']
