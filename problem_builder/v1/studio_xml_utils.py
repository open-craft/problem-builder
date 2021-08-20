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
The mentoring XBlock was previously designed to be edited using XML.

This file contains a hack necessary for us to parse the old XML data and create blocks in Studio
from the parsed XML, as part of the upgrade process.

It works by parsing the XML and creating XBlocks in a temporary runtime
environment, so that the blocks' fields can be read and copied into Studio.
"""

from xblock.fields import Scope
from xblock.runtime import (DictKeyValueStore, KvsFieldData, MemoryIdManager,
                            Runtime, ScopeIds)


class TransientRuntime(Runtime):
    """
    An XBlock runtime designed to have no persistence and no ability to render views/handlers.
    """
    def __init__(self):
        id_manager = MemoryIdManager()
        field_data = KvsFieldData(DictKeyValueStore())
        super().__init__(
            id_reader=id_manager,
            id_generator=id_manager,
            field_data=field_data,
        )

    def create_block_from_node(self, node):
        """
        Parse an XML node representing an XBlock (and children), and return the XBlock.
        """
        block_type = node.tag
        def_id = self.id_generator.create_definition(block_type)
        usage_id = self.id_generator.create_usage(def_id)
        keys = ScopeIds(None, block_type, def_id, usage_id)
        block_class = self.mixologist.mix(self.load_block_type(block_type))
        block = block_class.parse_xml(node, self, keys, self.id_generator)
        block.save()
        return block

    def handler_url(self, *args, **kwargs):
        raise NotImplementedError("TransientRuntime does not support handler_url.")

    def local_resource_url(self, *args, **kwargs):
        raise NotImplementedError("TransientRuntime does not support local_resource_url.")

    def publish(self, *args, **kwargs):
        raise NotImplementedError("TransientRuntime does not support publish.")

    def resource_url(self, *args, **kwargs):
        raise NotImplementedError("TransientRuntime does not support resource_url.")

    def render_template(self, *args, **kwargs):
        raise NotImplementedError("TransientRuntime cannot render templates.")


def studio_update_from_node(block, node):
    """
    Given an XBlock that is using the edX Studio runtime, replace all of block's fields and
    children with the fields and children defined by the XML node 'node'.
    """

    user_id = block.runtime.user_id
    temp_runtime = TransientRuntime()
    source_block = temp_runtime.create_block_from_node(node)

    def update_from_temp_block(real_block, temp_block):
        """
        Recursively copy all fields and children from temp_block to real_block.
        """
        # Fields:
        for field_name, field in temp_block.fields.items():
            if field.scope in (Scope.content, Scope.settings) and field.is_set_on(temp_block):
                setattr(real_block, field_name, getattr(temp_block, field_name))
        # Children:
        if real_block.has_children:
            real_block.children = []
            for child_id in temp_block.children:
                child = temp_block.runtime.get_block(child_id)
                new_child = real_block.runtime.modulestore.create_item(
                    user_id, real_block.location.course_key, child.scope_ids.block_type
                )
                update_from_temp_block(new_child, child)
                real_block.children.append(new_child.location)
        real_block.save()
        real_block.runtime.modulestore.update_item(real_block, user_id)

    with block.runtime.modulestore.bulk_operations(block.location.course_key):
        for child_id in block.children:
            block.runtime.modulestore.delete_item(child_id, user_id)
        update_from_temp_block(block, source_block)
