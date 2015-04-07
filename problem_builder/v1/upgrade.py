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
The mentoring XBlock was previously designed to be edited using XML.

This file contains a script to help migrate mentoring blocks to the new format which is
optimized for editing in Studio.

To run the script on devstack:
SERVICE_VARIANT=cms DJANGO_SETTINGS_MODULE="cms.envs.devstack" python -m problem_builder.v1.upgrade [course id here]
"""
import logging
from lxml import etree
from mentoring import MentoringBlock
from problem_builder import MentoringBlock as NewMentoringBlock
from StringIO import StringIO
import sys
import warnings
from courseware.models import StudentModule
from .studio_xml_utils import studio_update_from_node
from .xml_changes import convert_xml_v1_to_v2


def upgrade_block(block):
    """
    Given a MentoringBlock "block" with old-style (v1) data in its "xml_content" field, parse
    the XML and re-create the block with new-style (v2) children and settings.
    """
    assert isinstance(block, (MentoringBlock, NewMentoringBlock))
    assert bool(block.xml_content)  # If it's a v1 block it will have xml_content
    store = block.runtime.modulestore
    xml_content_str = block.xml_content
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(StringIO(xml_content_str), parser=parser).getroot()
    assert root.tag == "mentoring"
    with warnings.catch_warnings(record=True) as warnings_caught:
        warnings.simplefilter("always")
        convert_xml_v1_to_v2(root)
        for warning in warnings_caught:
            print(u"    ➔ {}".format(str(warning.message)))

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
                if isinstance(child.tag, basestring):
                    block.data += etree.tostring(child)
            return block
        HtmlDescriptor.parse_xml = parse_xml_for_HtmlDescriptor

    # Save the xml_content to make this processes rerunnable, in case it doesn't work correctly the first time.
    root.attrib["xml_content"] = xml_content_str

    # Was block already published?
    parent = block.runtime.get_block(block.parent)  # Don't use get_parent() as it may be an outdated cached version
    parent_was_published = not store.has_changes(parent)

    old_usage_id = block.location
    if old_usage_id.block_type != "problem-builder":
        # We need to change the block type from "mentoring" to "problem-builder", which requires
        # deleting then re-creating the block:
        store.delete_item(old_usage_id, user_id=None)
        parent_children = parent.children
        index = parent_children.index(old_usage_id)

        url_name = unicode(old_usage_id.block_id)
        if "url_name" in root.attrib:
            url_name_xml = root.attrib.pop("url_name")
            if url_name != url_name_xml:
                print(u"    ➔ Two conflicting url_name values! Using the 'real' one : {}".format(url_name))
                print(u"    ➔ References to the old url_name ({}) need to be updated manually.".format(url_name_xml))
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
        print(u"    ➔ problem-builder created: {}".format(url_name))

        # Now we've changed the block's block_type but in doing so we've disrupted the student data.
        # Migrate it now:
        student_data = StudentModule.objects.filter(module_state_key=old_usage_id)
        num_entries = student_data.count()
        if num_entries > 0:
            print(u"    ➔ Migrating {} student records to new block".format(num_entries))
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

    print(u"┏━━━━━━━━━━━━━━━━━━━━━━━━━━┓")
    print(u"┃ Mentoring Upgrade Script ┃")
    print(u"┗━━━━━━━━━━━━━━━━━━━━━━━━━━┛")

    try:
        course_id = CourseKey.from_string(sys.argv[1])
    except (IndexError, InvalidKeyError):
        sys.exit("Need a course ID argument like 'HarvardX/GSE1.1x/3T2014' or 'course-v1:HarvardX+B101+2015'")

    store = modulestore()
    course = store.get_course(course_id)
    if course is None:
        sys.exit(u"Course '{}' not found.".format(unicode(course_id)))
    print(u" ➔ Found course: {}".format(course.display_name))
    print(u" ➔ Searching for mentoring blocks")
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
    print(u" ➔ Found {} mentoring blocks".format(total))

    print(u" ➔ Doing a quick sanity check of the url_names")
    url_names = set()
    stop = False
    for block_id in blocks_found:
        url_name = block_id.block_id
        block = course.runtime.get_block(block_id)
        if url_name in url_names:
            print(u" ➔ Mentoring block {} appears in the course in multiple places!".format(url_name))
            print(u'   (display_name: "{}", parent {}: "{}")'.format(
                block.display_name, block.parent, block.get_parent().display_name
            ))
            print(u'   To fix, you must delete the extra occurences.')
            stop = True
            continue
        if block.url_name and block.url_name != unicode(block_id.block_id):
            print(u" ➔ Warning: Mentoring block {} has a different url_name set in the XML.".format(url_name))
            print(u"   If other blocks reference this block using the XML url_name '{}',".format(block.url_name))
            print(u"   those blocks will need to be updated.")
            if "--force" not in sys.argv:
                print(u"   In order to force this upgrade to continue, add --force to the end of the command.")
                stop = True
        url_names.add(url_name)

    if stop:
        sys.exit(u" ➔ Exiting due to errors preventing the upgrade.")

    with store.bulk_operations(course.location.course_key):
        count = 1
        for block_id in blocks_found:
            block = course.runtime.get_block(block_id)
            print(u" ➔ Upgrading block {} of {} - \"{}\"".format(count, total, block.url_name))
            count += 1
            upgrade_block(block)

    print(u" ➔ Complete.")
