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
"""
Test that we can upgrade from mentoring v1 to problem builder (v2).
"""
import os.path
import unittest

import ddt
from lxml import etree
from six import StringIO
from xblock.core import XBlock
from xblock.fields import ScopeIds
from xblock.runtime import DictKeyValueStore, KvsFieldData
from xblock.test.tools import TestRuntime

from problem_builder.mentoring import MentoringBlock
from problem_builder.v1.xml_changes import convert_xml_to_v2
from sample_xblocks.basic.content import HtmlBlock

xml_path = os.path.join(os.path.dirname(__file__), "xml")


@ddt.ddt
class TestUpgrade(unittest.TestCase):
    """
    Test upgrade from mentoring v1 (which uses xml_content even in Studio) to v2.

    We can't test the steps that depend on Studio, so we just test the XML conversion.
    """

    def setUp(self):
        self.runtime = TestRuntime(field_data=KvsFieldData(DictKeyValueStore()))

    @ddt.data(
        "v1_upgrade_a",
        "v1_upgrade_b",
        "v1_upgrade_c",
    )
    @XBlock.register_temp_plugin(HtmlBlock, "html")
    @XBlock.register_temp_plugin(MentoringBlock, "mentoring")
    def test_xml_upgrade(self, file_name):
        """
        Convert a v1 mentoring block to v2 and then compare the resulting block to a pre-converted one.
        """
        with open("{}/{}_old.xml".format(xml_path, file_name)) as xmlfile:
            temp_node = etree.parse(xmlfile).getroot()
            old_block = self.create_block_from_node(temp_node)

        parser = etree.XMLParser(remove_blank_text=True)
        xml_root = etree.parse(StringIO(old_block.xml_content), parser=parser).getroot()
        convert_xml_to_v2(xml_root)
        converted_block = self.create_block_from_node(xml_root)

        with open("{}/{}_new.xml".format(xml_path, file_name)) as xmlfile:
            temp_node = etree.parse(xmlfile).getroot()
            new_block = self.create_block_from_node(temp_node)

        try:
            self.assertBlocksAreEquivalent(converted_block, new_block)
        except AssertionError:
            xml_result = etree.tostring(xml_root, pretty_print=True, encoding="UTF-8")
            print("Converted XML:\n{}".format(xml_result))
            raise

    def create_block_from_node(self, node):
        """
        Parse an XML node representing an XBlock (and children), and return the XBlock.
        """
        block_type = node.tag
        def_id = self.runtime.id_generator.create_definition(block_type)
        usage_id = self.runtime.id_generator.create_usage(def_id)
        keys = ScopeIds(None, block_type, def_id, usage_id)
        block_class = self.runtime.mixologist.mix(self.runtime.load_block_type(block_type))
        block = block_class.parse_xml(node, self.runtime, keys, self.runtime.id_generator)
        block.save()
        return block

    def assertBlocksAreEquivalent(self, block1, block2):
        """
        Compare two blocks for equivalence.
        Borrowed from xblock.test.tools.blocks_are_equivalent but modified to use assertions.
        """
        # The two blocks have to be the same class.
        self.assertEqual(block1.__class__, block2.__class__)
        # They have to have the same fields.
        self.assertEqual(set(block1.fields), set(block2.fields))
        # The data fields have to have the same values.
        for field_name in block1.fields:
            if field_name in ('parent', 'children'):
                continue
            if field_name == "content":
                # Inner HTML/XML content may have varying whitespace which we don't care about:
                self.assertEqual(
                    self.clean_html(getattr(block1, field_name)),
                    self.clean_html(getattr(block2, field_name))
                )
            else:
                self.assertEqual(getattr(block1, field_name), getattr(block2, field_name))
        # The children need to be equal.
        self.assertEqual(block1.has_children, block2.has_children)

        if block1.has_children:
            self.assertEqual(len(block1.children), len(block2.children))
            for child_id1, child_id2 in zip(block1.children, block2.children):
                # Load up the actual children to see if they are equal.
                child1 = block1.runtime.get_block(child_id1)
                child2 = block2.runtime.get_block(child_id2)
                self.assertBlocksAreEquivalent(child1, child2)

    def clean_html(self, html_str):
        """
        Standardize the given HTML string for a consistent comparison.
        Assumes the HTML is valid XML.
        """
        # We wrap it in <x></x> so that the given HTML string doesn't need a single root element.
        parser = etree.XMLParser(remove_blank_text=True)
        parsed = etree.parse(StringIO(u"<x>{}</x>".format(html_str)), parser=parser).getroot()
        return etree.tostring(parsed, pretty_print=False, encoding="UTF-8")[3:-3]
