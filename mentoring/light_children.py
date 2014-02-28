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

from cStringIO import StringIO
from lxml import etree

from xblock.core import XBlock
from xblock.fragment import Fragment
from xblock.plugin import Plugin

from .utils import XBlockWithChildrenFragmentsMixin


# Globals ###########################################################

log = logging.getLogger(__name__)


# Classes ###########################################################

class LightChildrenMixin(XBlockWithChildrenFragmentsMixin):
    """
    Allows to use lightweight children on a given XBlock, which will
    have a similar behavior but will not be instanciated as full-fledged
    XBlocks, which aren't correctly supported as children

    TODO: Replace this once the support for XBlock children has matured
    by a mixin implementing the following abstractions, used to keep
    code reusable in the XBlocks:

    * get_children_objects()
    * Functionality of XBlockWithChildrenFragmentsMixin

    Other changes caused by LightChild use:

    * overrides of `parse_xml()` have been replaced by overrides of
    `init_block_from_node()` on LightChildren
    * fields on LightChild don't have any persistence
    """

    @classmethod
    def parse_xml(cls, node, runtime, keys, id_generator):
        block = runtime.construct_xblock_from_class(cls, keys)
        cls.init_block_from_node(block, node, node.items())
        block.xml_content = getattr(block, 'xml_content', '') or etree.tostring(node)
        return block

    @classmethod
    def init_block_from_node(cls, block, node, attr):
        block.light_children = []
        for child_id, xml_child in enumerate(node):
            cls.add_node_as_child(block, xml_child, child_id)

        for name, value in attr:
            setattr(block, name, value)

        return block

    @classmethod
    def add_node_as_child(cls, block, xml_child, child_id):
        # Instantiate child
        child_class = cls.get_class_by_element(xml_child.tag)
        child = child_class(block.runtime)
        child.name = u'{}_{}'.format(block.name, child_id)

        # Add any children the child may itself have
        child_class.init_block_from_node(child, xml_child, xml_child.items())

        text = xml_child.text
        if text:
            text = text.strip()
            if text:
                child.content = text

        block.light_children.append(child)

    @classmethod
    def get_class_by_element(cls, xml_tag):
        return LightChild.load_class(xml_tag)

    def load_children_from_xml_content(self):
        """
        Load light children from the `xml_content` attribute
        """
        self.light_children = []
        if not hasattr(self, 'xml_content') or not self.xml_content:
            return

        node = etree.parse(StringIO(self.xml_content)).getroot()
        LightChildrenMixin.init_block_from_node(self, node, {})

    def get_children_objects(self):
        """
        Replacement for ```[self.runtime.get_block(child_id) for child_id in self.children]```
        """
        return self.light_children

    def render_child(self, child, view_name, context):
        """
        Replacement for ```self.runtime.render_child()```
        """
        frag = getattr(child, view_name)(context)
        frag.content = u'<div class="xblock-light-child" name="{}" data-type="{}">{}</div>'.format(
                child.name, child.__class__.__name__, frag.content)
        return frag

    def get_children_fragment(self, context, view_name='student_view', instance_of=None,
                              not_instance_of=None):
        fragment = Fragment()
        named_child_frags = []
        for child in self.get_children_objects():
            if instance_of is not None and not isinstance(child, instance_of):
                continue
            if not_instance_of is not None and isinstance(child, not_instance_of):
                continue
            frag = self.render_child(child, view_name, context)
            fragment.add_frag_resources(frag)
            named_child_frags.append((child.name, frag))
        return fragment, named_child_frags


class XBlockWithLightChildren(LightChildrenMixin, XBlock):
    """
    XBlock base class with support for LightChild
    """
    def __init__(self, *args, **kwargs):
        super(XBlockWithLightChildren, self).__init__(*args, **kwargs)
        self.load_children_from_xml_content()


class LightChild(Plugin, LightChildrenMixin):
    """
    Base class for the light children
    """
    entry_point = 'xblock.light_children'

    def __init__(self, runtime):
        self.runtime = runtime

    def save(self):
        pass


class LightChildField(object):
    """
    Fake field with no persistence - allows to keep XBlocks fields definitions on LightChild
    """
    def __init__(self, *args, **kwargs):
        self.value = kwargs.get('default', '')

    def __nonzero__(self):
        return bool(self.value)


class String(LightChildField):
    def __init__(self, *args, **kwargs):
        self.value = kwargs.get('default', '') or ''

    def __str__(self):
        return self.value

    def split(self, *args, **kwargs):
        return self.value.split(*args, **kwargs)


class Boolean(LightChildField):
    pass

class Scope(object):
    content = None
    user_state = None
