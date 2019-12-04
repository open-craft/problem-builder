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

# Imports ###########################################################

import uuid

import six
from lxml import etree
from xblock.core import XBlock
from xblock.fields import Scope, String
from xblock.fragment import Fragment
from xblock.validation import ValidationMessage
from xblockutils.studio_editable import (StudioEditableXBlockMixin,
                                         XBlockWithPreviewMixin)

from problem_builder.mixins import (ExpandStaticURLMixin,
                                    StudentViewUserStateMixin,
                                    XBlockWithTranslationServiceMixin)


# Make '_' a no-op so we can scrape strings
def _(text):
    return text

# Classes ###########################################################


@XBlock.needs("i18n")
class ChoiceBlock(
    StudioEditableXBlockMixin, XBlockWithPreviewMixin, XBlockWithTranslationServiceMixin, StudentViewUserStateMixin,
    XBlock, ExpandStaticURLMixin
):
    """
    Custom choice of an answer for a MCQ/MRQ
    """
    value = String(
        display_name=_("Value"),
        help=_("Value of the choice when selected. Should be unique. Generally you do not need to edit this."),
        scope=Scope.content,
        default="",
    )
    content = String(
        display_name=_("Choice Text"),
        help=_("Human-readable version of the choice value"),
        scope=Scope.content,
        default="",
    )
    editable_fields = ('content', 'value')

    @property
    def display_name_with_default(self):
        try:
            status = self.get_parent().describe_choice_correctness(self.value)
        except Exception:
            status = self._(u"Out of Context")  # Parent block should implement describe_choice_correctness()
        return self._(u"Choice ({status})").format(status=status)

    def student_view_data(self, context=None):
        """
        Returns a JSON representation of the student_view of this XBlock,
        retrievable from the Course Block API.
        """
        # display_name_with_default gives out correctness - not adding it here
        return {
            'block_id': six.text_type(self.scope_ids.usage_id),
            'display_name': self.expand_static_url(self._(u"Choice ({content})").format(content=self.content)),
            'value': self.value,
            'content': self.expand_static_url(self.content),
        }

    def mentoring_view(self, context=None):
        """ Render this choice string within a mentoring block question. """
        return Fragment(u'<span class="choice-text">{}</span>'.format(self.content))

    def student_view(self, context=None):
        """ Normal view of this XBlock, identical to mentoring_view """
        return self.mentoring_view(context)

    def validate_field_data(self, validation, data):
        """
        Validate this block's field data.
        """
        super(ChoiceBlock, self).validate_field_data(validation, data)

        def add_error(msg):
            validation.add(ValidationMessage(ValidationMessage.ERROR, msg))

        if not data.value.strip():
            add_error(self._(u"No value set. This choice will not work correctly."))
        if not data.content.strip():
            add_error(self._(u"No choice text set yet."))

    def validate(self):
        """
        Validates the state of this XBlock.
        """
        validation = super(ChoiceBlock, self).validate()
        if self.get_parent().all_choice_values.count(self.value) > 1:
            validation.add(
                ValidationMessage(ValidationMessage.ERROR, self._(
                    u"This choice has a non-unique ID and won't work properly. "
                    "This can happen if you duplicate a choice rather than use the Add Choice button."
                ))
            )
        print(self.get_parent().all_choice_values)
        return validation

    @classmethod
    def get_template(cls, template_id):
        """
        Used to interact with Studio's create_xblock method to instantiate pre-defined templates.
        """
        # Generate a random 'value' value. We can't just use default=UNIQUE_ID on the field,
        # because that doesn't work properly with import/export, re-run, or duplicating the block
        if template_id == 'studio_default':
            return {'data': {'value': uuid.uuid4().hex[:7]}}
        return {'metadata': {}, 'data': {}}

    @classmethod
    def parse_xml(cls, node, runtime, keys, id_generator):
        """
        Construct this XBlock from the given XML node.
        """
        block = runtime.construct_xblock_from_class(cls, keys)
        for field_name in ('value', 'content'):
            if field_name in node.attrib:
                setattr(block, field_name, node.attrib[field_name])

        # HTML content:
        block.content = six.text_type(node.text or u"")
        for child in node:
            block.content += etree.tostring(child, encoding='unicode')

        return block
