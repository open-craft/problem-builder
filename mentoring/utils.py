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
    def get_children_fragment(self, context, view_name='student_view', instance_of=None,
                              not_instance_of=None):
        """
        Returns a global fragment containing the resources used by the children views,
        and a list of fragments, one per children

        - `view_name` allows to select a specific view method on the children
        - `instance_of` allows to only return fragments for children which are instances of 
          the provided class
        - `not_instance_of` allows to only return fragments for children which are *NOT* 
          instances of the provided class
        """
        fragment = Fragment()
        named_child_frags = []
        for child_id in self.children:  # pylint: disable=E1101
            child = self.runtime.get_block(child_id)
            if instance_of is not None and not isinstance(child, instance_of):
                continue
            if not_instance_of is not None and isinstance(child, not_instance_of):
                continue
            frag = self.runtime.render_child(child, view_name, context)
            fragment.add_frag_resources(frag)
            named_child_frags.append((child.name, frag))
        return fragment, named_child_frags

    def children_view(self, context, view_name='children_view'):
        """
        Returns a fragment with the content of all the children's content, concatenated
        """
        fragment, named_children = self.get_children_fragment(context)
        for name, child_fragment in named_children:
            fragment.add_content(child_fragment.content)
        return fragment
