# -*- coding: utf-8 -*-

# Imports ###########################################################

import logging
import os

from xblock.core import XBlock
from xblock.fields import Boolean, Scope, String

from .utils import load_resource, render_template, XBlockWithChildrenFragmentsMixin


# Globals ###########################################################

log = logging.getLogger(__name__)


# Classes ###########################################################

class MentoringBlock(XBlock, XBlockWithChildrenFragmentsMixin):
    """
    An XBlock providing mentoring capabilities

    Composed of text, answers input fields, and a set of multiple choice quizzes with advices. 
    A set of conditions on the provided answers and quizzes choices will determine if the
    student is a) provided mentoring advices and asked to alter his answer, or b) is given the
    ok to continue.
    """
    attempted = Boolean(help="Has the student attempted this mentoring step?", default=False, scope=Scope.user_state)
    completed = Boolean(help="Has the student completed this mentoring step?", default=False, scope=Scope.user_state)
    completed_message = String(help="Message to display upon completion", scope=Scope.content, default="")
    has_children = True

    @classmethod
    def parse_xml(cls, node, runtime, keys):
        block = runtime.construct_xblock_from_class(cls, keys)

        for child in node:
            if child.tag == 'message':
                if child.get('type') == 'completed':
                    block.completed_message = child.text
                else:
                    raise ValueError, u'Invalid value for message type: `{}`'.format(child.get('type'))
            else:
                block.runtime.add_node_as_child(block, child)

        for name, value in node.items():
            if name in block.fields:
                setattr(block, name, value)

        return block

    def student_view(self, context):
        fragment, named_children = self.get_children_fragment(context, view_name='mentoring_view')

        fragment.add_content(render_template('templates/html/mentoring.html', {
            'self': self,
            'named_children': named_children,
        }))
        fragment.add_css(load_resource('static/css/mentoring.css'))
        fragment.add_javascript(load_resource('static/js/vendor/underscore-min.js'))
        fragment.add_javascript(load_resource('static/js/mentoring.js'))

        # TODO-LMS-WORKAROUND: Use self.runtime.resources_url() when supported
        fragment.add_resource(load_resource('templates/html/mentoring_progress.html').format(
                completed='/static/images/correct-icon.png'),
            "text/html")

        fragment.initialize_js('MentoringBlock')

        return fragment

    @XBlock.json_handler
    def submit(self, submissions, suffix=''):
        log.info(u'Received submissions: {}'.format(submissions))
        self.attempted = True

        submit_results = []
        completed = True
        for child_id in self.children:  # pylint: disable=E1101
            child = self.runtime.get_block(child_id)
            if child.name and child.name in submissions:
                submission = submissions[child.name]
                child_result = child.submit(submission)
                submit_results.append([child.name, child_result])
                child.save()
                completed = completed and child_result['completed']

        self.completed = bool(completed)
        if self.completed:
            message = self.completed_message
        else:
            message = ''

        return {
            'submitResults': submit_results,
            'completed': self.completed,
            'message': message,
        }

    @staticmethod
    def workbench_scenarios():
        """
        Scenarios displayed by the workbench. Load them from external (private) repository
        """
        templates_path = 'templates/xml'
        base_fullpath = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        templates_fullpath = os.path.join(base_fullpath, templates_path)

        scenarios = []
        for template in os.listdir(templates_fullpath):
            if not template.endswith('.xml'):
                continue
            title = template[:-4].replace('_', ' ').title()
            template_path = os.path.join(templates_path, template)
            scenarios.append((title, load_resource(template_path)))

        return scenarios
