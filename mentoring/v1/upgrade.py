# -*- coding: utf-8 -*-
"""
The mentoring XBlock was previously designed to be edited using XML.

This file contains a script to help migrate mentoring blocks to the new format which is
optimized for editing in Studio.

To run the script on devstack:
SERVICE_VARIANT=cms DJANGO_SETTINGS_MODULE="cms.envs.devstack" python -m mentoring.v1.upgrade
"""
import logging
from lxml import etree
from mentoring import MentoringBlock
from StringIO import StringIO
import sys
from courseware.models import StudentModule
from xmodule.modulestore.exceptions import DuplicateItemError
from .studio_xml_utils import studio_update_from_node
from .xml_changes import convert_xml_v1_to_v2


def upgrade_block(block):
    """
    Given a MentoringBlock "block" with old-style (v1) data in its "xml_content" field, parse
    the XML and re-create the block with new-style (v2) children and settings.
    """
    assert isinstance(block, MentoringBlock)
    assert bool(block.xml_content)  # If it's a v1 block it will have xml_content
    store = block.runtime.modulestore
    xml_content_str = block.xml_content
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(StringIO(xml_content_str), parser=parser).getroot()
    assert root.tag == "mentoring"
    convert_xml_v1_to_v2(root)

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
    parent = block.get_parent()
    parent_was_published = not store.has_changes(parent)

    # If the block has a url_name attribute that doesn't match Studio's url_name, fix that:
    delete_on_success = None
    if "url_name" in root.attrib:
        url_name = root.attrib.pop("url_name")
        if block.url_name != url_name:
            print(" ➔ This block has two conflicting url_name values set. Attempting to fix...")
            # Fix the url_name by replacing the block with a blank block with the correct url_name
            parent_children = parent.children
            old_usage_id = block.location
            index = parent_children.index(old_usage_id)
            try:
                new_block = store.create_item(
                    user_id=None,
                    course_key=block.location.course_key,
                    block_type="mentoring",
                    block_id=url_name,
                    fields={"xml_content": xml_content_str},
                )
                delete_on_success = block
                parent_children[index] = new_block.location
                parent.save()
                store.update_item(parent, user_id=None)
                block = new_block
                print(" ➔ url_name changed to {}".format(url_name))
                # Now we've fixed the block's url_name but in doing so we've disrupted the student data.
                # Migrate it now:
                student_data = StudentModule.objects.filter(module_state_key=old_usage_id)
                num_entries = student_data.count()
                if num_entries > 0:
                    print(" ➔ Migrating {} student records to new url_name".format(num_entries))
                    student_data.update(module_state_key=new_block.location)
            except DuplicateItemError:
                print(
                    "\n WARNING: The block with url_name '{}' doesn't match "
                    "the real url_name '{}' and auto repair failed.\n".format(
                        url_name, block.url_name
                    )
                )

    # Replace block with the new version and the new children:
    studio_update_from_node(block, root)

    if delete_on_success:
        store.delete_item(delete_on_success.location, user_id=None)
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

    store = modulestore()
    course = store.get_course(course_id)
    if course is None:
        sys.exit(u"Course '{}' not found.".format(unicode(course_id)))
    print(" ➔ Found course: {}".format(course.display_name))
    print(" ➔ Searching for mentoring blocks")
    blocks_found = []

    def find_mentoring_blocks(block):
        if isinstance(block, MentoringBlock) and block.xml_content:  # If it's a v1 block it will have xml_content
            blocks_found.append(block.scope_ids.usage_id)
        elif block.has_children:
            for child_id in block.children:
                find_mentoring_blocks(block.runtime.get_block(child_id))
    find_mentoring_blocks(course)
    total = len(blocks_found)
    print(" ➔ Found {} mentoring blocks".format(total))

    with store.bulk_operations(course.location.course_key):
        count = 1
        for block_id in blocks_found:
            block = course.runtime.get_block(block_id)
            print(" ➔ Upgrading block {} of {} - \"{}\"".format(count, total, block.url_name))
            count += 1
            upgrade_block(block)

    print(" ➔ Complete.")
