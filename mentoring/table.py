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
        fragment, columns_frags = self.get_children_fragment(context,
                                                             view_name='mentoring_table_view')
        f, header_frags = self.get_children_fragment(context, view_name='mentoring_table_header_view')

        # TODO: What's the right way to link to images from CSS? This hack won't work in prod
        bg_image_url = self.runtime.resources_url('mentoring/img/{}-bg.png'.format(self.type))

        fragment.add_content(render_template('templates/html/mentoring-table.html', {
            'self': self,
            'columns_frags': columns_frags,
            'header_frags': header_frags,
            'bg_image_url': bg_image_url,
        }))
        fragment.add_css(load_resource('static/css/mentoring-table.css'))
        fragment.add_javascript(load_resource('static/js/vendor/jquery.shorten.js'))
        fragment.add_javascript(load_resource('static/js/mentoring-table.js'))
        fragment.initialize_js('MentoringTableBlock')

        return fragment

    def mentoring_view(self, context):
        # Allow to render within mentoring blocks, or outside
        return self.student_view(context)


class MentoringTableColumnBlock(XBlock, XBlockWithChildrenFragmentsMixin):
    """
    Individual column of a mentoring table
    """
    header = String(help="Header of the column", scope=Scope.content, default=None)
    has_children = True

    def student_view(self, context=None):  # pylint: disable=W0613
        """Returns default student view."""
        return Fragment(u"<p>I can only appear inside mentoring-table blocks.</p>")

    def mentoring_table_view(self, context):
        """
        The content of the column
        """
        fragment, named_children = self.get_children_fragment(context,
                                              view_name='mentoring_table_view',
                                              not_instance_of=MentoringTableColumnHeaderBlock)
        fragment.add_content(render_template('templates/html/mentoring-table-column.html', {
            'self': self,
            'named_children': named_children,
        }))
        return fragment

    def mentoring_table_header_view(self, context):
        """
        The content of the column's header
        """
        fragment, named_children = self.get_children_fragment(context,
                                              view_name='mentoring_table_header_view',
                                              instance_of=MentoringTableColumnHeaderBlock)
        fragment.add_content(render_template('templates/html/mentoring-table-header.html', {
            'self': self,
            'named_children': named_children,
        }))
        return fragment


class MentoringTableColumnHeaderBlock(XBlock, XBlockWithChildrenFragmentsMixin):
    """
    Header content for a given column
    """
    content = String(help="Body of the header", scope=Scope.content, default='')
    has_children = True
    
    def student_view(self, context=None):  # pylint: disable=W0613
        """Returns default student view."""
        return Fragment(u"<p>I can only appear inside mentoring-table blocks.</p>")

    def mentoring_table_header_view(self, context):
        fragment = super(MentoringTableColumnHeaderBlock, self).children_view(context)
        fragment.add_content(unicode(self.content))
        return fragment

