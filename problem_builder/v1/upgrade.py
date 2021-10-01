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

This file contains a script to help migrate mentoring blocks to the new format which is
optimized for editing in Studio.

To run the script on devstack:
SERVICE_VARIANT=cms DJANGO_SETTINGS_MODULE="cms.envs.devstack" python -m problem_builder.v1.upgrade [course id here]

You can add "--version=v0" at the end of the command to upgrade from the oldest xblock-mentoring
instance which was kept on gsehub's GitHub account.
"""
import logging
import sys
import warnings

from lxml import etree
from mentoring import MentoringBlock
from six import StringIO

from problem_builder.mentoring import MentoringBlock as NewMentoringBlock

from .platform_dependencies import StudentModule
from .studio_xml_utils import studio_update_from_node
from .xml_changes import convert_xml_to_v2

if not StudentModule:
    raise ImportError("Could not import StudentModule from edx-platform courseware app.")


def upgrade_block(store, block, from_version="v1"):
    """
    Given a MentoringBlock "block" with old-style (v1) data in its "xml_content" field, parse
    the XML and re-create the block with new-style (v2) children and settings.
    """
    assert isinstance(block, (MentoringBlock, NewMentoringBlock))
    assert bool(block.xml_content)  # If it's a v1 block it will have xml_content
    xml_content_str = block.xml_content
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(StringIO(xml_content_str), parser=parser).getroot()
    assert root.tag == "mentoring"
    with warnings.catch_warnings(record=True) as warnings_caught:
        warnings.simplefilter("always")
        convert_xml_to_v2(root, from_version=from_version)
        for warning in warnings_caught:
            print(f"    ➔ {str(warning.message)}")

    # We need some special-case handling to deal with HTML being an XModule and not a pure XBlock:
    try:
        from xmodule.html_module import HtmlDescriptor
    except ImportError:
        pass  # Perhaps HtmlModule has been converted to an XBlock?
    else:
        @classmethod
        def parse_xml_for_HtmlDescriptor(cls, node, runtime, keys, id_generator):
            block = runtime.construct_xblock_from_class(cls, keys)
            block.data = node.text if node.text else ""
            for child in list(node):
                if isinstance(child.tag, str):
                    block.data += etree.tostring(child)
            return block
        HtmlDescriptor.parse_xml = parse_xml_for_HtmlDescriptor

    # Save the xml_content to make this processes rerunnable, in case it doesn't work correctly the first time.
    root.attrib["xml_content"] = xml_content_str

    # Was block already published?
    parent = store.get_item(block.parent)  # Don't use get_parent()/get_block() as it may be an outdated cached version
    assert getattr(parent.location, 'branch', None) is None
    assert getattr(parent.location, 'version_guid', None) is None
    assert getattr(parent.children[0], 'branch', None) is None
    assert getattr(parent.children[0], 'version_guid', None) is None
    parent_was_published = not store.has_changes(parent)

    old_usage_id = block.location
    if old_usage_id.block_type != "problem-builder":
        # We need to change the block type from "mentoring" to "problem-builder", which requires
        # deleting then re-creating the block:
        store.delete_item(old_usage_id, user_id=None)
        parent_children = parent.children
        index = parent_children.index(old_usage_id)

        url_name = str(old_usage_id.block_id)
        if "url_name" in root.attrib:
            url_name_xml = root.attrib.pop("url_name")
            if url_name != url_name_xml:
                print(f"    ➔ Two conflicting url_name values! Using the 'real' one : {url_name}")
                print(f"    ➔ References to the old url_name ({url_name_xml}) need to be updated manually.")
        block = store.create_item(
            user_id=None,
            course_key=old_usage_id.course_key,
            block_type="problem-builder",
            block_id=url_name,
            fields={"xml_content": xml_content_str},
        )
        parent_children[index] = block.location
        parent.save()
        store.update_item(parent, user_id=None)
        print(f"    ➔ problem-builder created: {url_name}")

        # Now we've changed the block's block_type but in doing so we've disrupted the student data.
        # Migrate it now:
        student_data = StudentModule.objects.filter(module_state_key=old_usage_id)
        num_entries = student_data.count()
        if num_entries > 0:
            print(f"    ➔ Migrating {num_entries} student records to new block")
            student_data.update(module_state_key=block.location)

    # Replace block with the new version and the new children:
    studio_update_from_node(block, root)

    if parent_was_published:
        store.publish(parent.location, user_id=None)


if __name__ == '__main__':
    # Disable some distracting overly-verbose warnings that we don't need:
    for noisy_module in ('edx.modulestore', 'elasticsearch', 'urllib3.connectionpool'):
        logging.getLogger(noisy_module).setLevel(logging.ERROR)
    from opaque_keys import InvalidKeyError
    from opaque_keys.edx.keys import CourseKey
    from xmodule.modulestore.django import modulestore

    print("┏━━━━━━━━━━━━━━━━━━━━━━━━━━┓")
    print("┃ Mentoring Upgrade Script ┃")
    print("┗━━━━━━━━━━━━━━━━━━━━━━━━━━┛")

    try:
        course_id = CourseKey.from_string(sys.argv[1])
    except (IndexError, InvalidKeyError):
        sys.exit("Need a course ID argument like 'HarvardX/GSE1.1x/3T2014' or 'course-v1:HarvardX+B101+2015'")

    from_version = "v1"
    if len(sys.argv) > 2:
        if sys.argv[2] == "--version=v0":
            from_version = "v0"
        else:
            sys.exit(f"invalid second argument: {' '.join(sys.argv[2:])}")

    store = modulestore()
    course = store.get_course(course_id)
    if course is None:
        sys.exit(f"Course '{str(course_id)}' not found.")
    print(f" ➔ Found course: {course.display_name}")
    print(" ➔ Searching for mentoring blocks")
    blocks_found = []

    def find_mentoring_blocks(block):
        """
        Find mentoring and recently-upgraded blocks. We check the recently upgraded ones
        in case an error happened and we're re-running the upgrade.
        """
        # If it's a v1 block or a recently upgraded block it will have xml_content:
        if isinstance(block, (MentoringBlock, NewMentoringBlock)) and block.xml_content:
            blocks_found.append(block.scope_ids.usage_id)
        elif block.has_children:
            for child_id in block.children:
                find_mentoring_blocks(block.runtime.get_block(child_id))
    find_mentoring_blocks(course)

    total = len(blocks_found)
    print(f" ➔ Found {total} mentoring blocks")

    print(" ➔ Doing a quick sanity check of the url_names")
    url_names = set()
    stop = False
    for block_id in blocks_found:
        url_name = block_id.block_id
        block = course.runtime.get_block(block_id)
        if url_name in url_names:
            print(f" ➔ Mentoring block {url_name} appears in the course in multiple places!")
            print(
                f'   (display_name: "{block.display_name}", parent {block.parent}:'
                f' "{block.get_parent().display_name)}")'
            )
            print('   To fix, you must delete the extra occurences.')
            stop = True
            continue
        if block.url_name and block.url_name != str(block_id.block_id):
            print(f" ➔ Warning: Mentoring block {url_name} has a different url_name set in the XML.")
            print(f"   If other blocks reference this block using the XML url_name '{block.url_name}',")
            print("   those blocks will need to be updated.")
            if "--force" not in sys.argv:
                print("   In order to force this upgrade to continue, add --force to the end of the command.")
                stop = True
        url_names.add(url_name)

    if stop:
        sys.exit(" ➔ Exiting due to errors preventing the upgrade.")

    with store.bulk_operations(course.location.course_key):
        count = 1
        for block_id in blocks_found:
            block = course.runtime.get_block(block_id)
            print(f" ➔ Upgrading block {count} of {total} - \"{block.url_name}\"")
            count += 1
            upgrade_block(store, block, from_version)

    print(" ➔ Complete.")
