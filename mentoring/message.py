# -*- coding: utf-8 -*-


# Imports ###########################################################

import logging

from xblock.core import XBlock
from xblock.fields import Scope, String
from xblock.fragment import Fragment

from .utils import render_template, XBlockWithChildrenFragmentsMixin


# Globals ###########################################################

log = logging.getLogger(__name__)


# Classes ###########################################################

class MentoringMessageBlock(XBlock, XBlockWithChildrenFragmentsMixin):
    """
    A message which can be conditionally displayed at the mentoring block level,
    for example upon completion of the block
    """
    content = String(help="Message to display upon completion", scope=Scope.content, default="")
    type = String(help="Type of message", scope=Scope.content, default="completed")
    has_children = True

    def student_view(self, context=None):  # pylint: disable=W0613
        """Returns default student view."""
        return Fragment(u"<p>I can only appear inside mentoring blocks.</p>")

    def mentoring_view(self, context=None):
        fragment, named_children = self.get_children_fragment(context, view_name='mentoring_view')
        fragment.add_content(render_template('templates/html/message.html', {
            'self': self,
            'named_children': named_children,
        }))
        return fragment
