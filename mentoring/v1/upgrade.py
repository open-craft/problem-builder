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
from .studio_xml_utils import studio_update_from_node
from .xml_changes import convert_xml_v1_to_v2


def upgrade_block(block):
    """
    Given a MentoringBlock "block" with old-style (v1) data in its "xml_content" field, parse
    the XML and re-create the block with new-style (v2) children and settings.
    """
    assert isinstance(block, MentoringBlock)
    assert bool(block.xml_content)  # If it's a v1 block it will have xml_content

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

    # Replace block with the new version and the new children:
    studio_update_from_node(block, root)


if __name__ == '__main__':
    # Disable some distracting overly-verbose warnings that we don't need:
    for noisy_module in ('edx.modulestore', 'elasticsearch', 'urllib3.connectionpool'):
        logging.getLogger(noisy_module).setLevel(logging.ERROR)
    from opaque_keys.edx.keys import CourseKey
    from xmodule.modulestore.django import modulestore

    print("┏━━━━━━━━━━━━━━━━━━━━━━━━━━┓")
    print("┃ Mentoring Upgrade Script ┃")
    print("┗━━━━━━━━━━━━━━━━━━━━━━━━━━┛")

    try:
        course_id = sys.argv[1]
    except IndexError:
        sys.exit("Need a course ID argument like 'HarvardX/GSE1.1x/3T2014' or 'course-v1:HarvardX+B101+2015'")

    store = modulestore()
    course = store.get_course(CourseKey.from_string(course_id))
    print(" ➔ Found course: {}".format(course.display_name))
    print(" ➔ Searching for mentoring blocks")
    blocks_found = []

    def find_mentoring_blocks(block):
        if isinstance(block, MentoringBlock):
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
