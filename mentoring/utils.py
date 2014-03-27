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

def get_scenarios_from_path(scenarios_path, include_identifier=False):
    """
    Returns an array of (title, xmlcontent) from files contained in a specified directory,
    formatted as expected for the return value of the workbench_scenarios() method
    """
    base_fullpath = os.path.dirname(os.path.realpath(__file__))
    scenarios_fullpath = os.path.join(base_fullpath, scenarios_path)

    scenarios = []
    if os.path.isdir(scenarios_fullpath):
        for template in os.listdir(scenarios_fullpath):
            if not template.endswith('.xml'):
                continue
            identifier = template[:-4]
            title = identifier.replace('_', ' ').title()
            template_path = os.path.join(scenarios_path, template)
            if not include_identifier:
                scenarios.append((title, load_resource(template_path)))
            else:
                scenarios.append((identifier, title, load_resource(template_path)))

    return scenarios

def load_scenarios_from_path(scenarios_path):
    """
    Load all xml files contained in a specified directory, as workbench scenarios
    """
    return get_scenarios_from_path(scenarios_path, include_identifier=True)


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
