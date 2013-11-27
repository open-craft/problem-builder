# -*- coding: utf-8 -*-

# Imports ###########################################################

import logging

from xblock.core import XBlock
from xblock.fields import Scope, String
from xblock.fragment import Fragment

from .utils import load_resource, render_template, XBlockWithChildrenFragmentsMixin


# Globals ###########################################################

log = logging.getLogger(__name__)


# Classes ###########################################################

class MentoringTableBlock(XBlock, XBlockWithChildrenFragmentsMixin):
    """
    Table-type display of information from mentoring blocks

    Used to present summary of information entered by the students in mentoring blocks.
    Supports different types of formatting through the `type` parameter.
    """
    type = String(help="Variant of the table to display", scope=Scope.content, default='')
    has_children = True

    def student_view(self, context):
        fragment, named_children = self.get_children_fragment(context, view_name='mentoring_table_view')

        fragment.add_content(render_template('templates/html/mentoring-table.html', {
            'self': self,
            'named_children': named_children,
        }))
        fragment.add_css(load_resource('static/css/mentoring-table.css'))

        return fragment

    @staticmethod
    def workbench_scenarios():
        """
        Sample scenarios which will be displayed in the workbench
        """
        return [
            ("Mentoring - Table 1, Test", load_resource('templates/xml/900_map.xml')),
        ]


class MentoringTableColumnBlock(XBlock, XBlockWithChildrenFragmentsMixin):
    """
    Individual column of a mentoring table
    """
    has_children = True

    def student_view(self, context=None):  # pylint: disable=W0613
        """Returns default student view."""
        return Fragment(u"<p>I can only appear inside mentoring-table blocks.</p>")

    def mentoring_table_view(self, context):
        fragment, named_children = self.get_children_fragment(context, view_name='mentoring_table_view')
        fragment.add_content(render_template('templates/html/mentoring-table-column.html', {
            'self': self,
            'named_children': named_children,
        }))
        return fragment

