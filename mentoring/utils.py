# -*- coding: utf-8 -*-


# Imports ###########################################################

import logging
import os
import pkg_resources
import unicodecsv

from cStringIO import StringIO
from django.template import Context, Template
from xblock.fragment import Fragment


# Globals ###########################################################

log = logging.getLogger(__name__)


# Functions #########################################################

def load_resource(resource_path):
    """
    Gets the content of a resource
    """
    resource_path = os.path.join('..', resource_path)
    resource_content = pkg_resources.resource_string(__name__, resource_path)
    return unicode(resource_content)

def render_template(template_path, context={}):
    """
    Evaluate a template by resource path, applying the provided context
    """
    template_str = load_resource(template_path)
    template = Template(template_str)
    return template.render(Context(context))

def list2csv(row):
    """
    Convert a list to a CSV string (single row)
    """
    f = StringIO()
    writer = unicodecsv.writer(f, encoding='utf-8')
    writer.writerow(row)
    f.seek(0)
    return f.read()


# Classes ###########################################################

class XBlockWithChildrenFragmentsMixin(object):
    def get_children_fragment(self, context, view_name='student_view'):
        fragment = Fragment()
        named_child_frags = []
        for child_id in self.children:  # pylint: disable=E1101
            child = self.runtime.get_block(child_id)
            frag = self.runtime.render_child(child, view_name, context)
            fragment.add_frag_resources(frag)
            named_child_frags.append((child.name, frag))
        return fragment, named_child_frags

