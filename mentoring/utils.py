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

import logging
import os
import pkg_resources
import unicodecsv

from cStringIO import StringIO
from django.template import Context, Template
from xblock.fragment import Fragment

from xblockutils.resources import ResourceLoader


log = logging.getLogger(__name__)


loader = ResourceLoader(__name__)


def load_resource(resource_path):
    return loader.load_unicode(resource_path)


def render_template(template_path, context={}):
    return loader.render_template(template_path, context)


def render_js_template(template_path, context={}, unique_id='light-child-template'):
    return loader.render_js_template(template_path, unique_id, context)


def get_scenarios_from_path(scenarios_path, include_identifier=False):
    return loader.load_scenarios_from_path(scenarios_path, include_identifier)


def load_scenarios_from_path(scenarios_path):
    return loader.load_scenarios_from_path(scenarios_path, include_identifier=True)


def list2csv(row):
    """
    Convert a list to a CSV string (single row)
    """
    f = StringIO()
    writer = unicodecsv.writer(f, encoding='utf-8')
    writer.writerow(row)
    f.seek(0)
    return f.read()


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
