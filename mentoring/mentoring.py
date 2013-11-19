# -*- coding: utf-8 -*-


# Imports ###########################################################

import logging

from xblock.core import XBlock
from xblock.fields import Boolean, Scope, String
from xblock.fragment import Fragment

from .utils import load_resource, render_template


# Globals ###########################################################

log = logging.getLogger(__name__)


# Classes ###########################################################

class MentoringBlock(XBlock):
    """
    An XBlock providing mentoring capabilities

    Each block is composed of a text prompt, an input field for a free answer from the student,
    and a set of multiple choice questions. The student submits his text answer, and is then asked
    the multiple-choice questions. A set of conditions on the answers provided to the multiple-
    choices will determine if the student is a) provided mentoring advices and asked to alter
    his answer, or b) is given the ok to continue.
    """

    prompt = String(help="Initial text displayed with the text input", default='Your answer?', scope=Scope.content)
    attempted = Boolean(help="Has the student attempted this mentoring step?", default=False, scope=Scope.user_state)
    completed = Boolean(help="Has the student completed this mentoring step?", default=False, scope=Scope.user_state)
    has_children = True

    def get_children_fragment(self, context):
        fragment = Fragment()
        named_child_frags = []
        for child_id in self.children:  # pylint: disable=E1101
            child = self.runtime.get_block(child_id)
            frag = self.runtime.render_child(child, "mentoring_view", context)
            fragment.add_frag_resources(frag)
            named_child_frags.append((child.name, frag))
        return fragment, named_child_frags

    def student_view(self, context):
        """
        Create a fragment used to display the XBlock to a student.
        `context` is a dictionary used to configure the display (unused)

        Returns a `Fragment` object specifying the HTML, CSS, and JavaScript
        to display.
        """
        fragment, named_children = self.get_children_fragment(context)

        fragment.add_content(render_template('static/html/mentoring.html', {
            'self': self,
            'named_children': named_children,
        }))
        fragment.add_css(load_resource('static/css/mentoring.css'))
        fragment.add_javascript(load_resource('static/js/mentoring.js'))
        fragment.initialize_js('MentoringBlock')

        return fragment

    @XBlock.json_handler
    def submit(self, submissions, suffix=''):
        log.info(u'Received submissions: {}'.format(submissions))
        self.attempted = True

        child_map = {}
        for child_id in self.children:  # pylint: disable=E1101
            child = self.runtime.get_block(child_id)
            if child.name:
                child_map[child.name] = child

        submit_results = {}
        completed = True
        for input_name, submission in submissions.items():
            child = child_map[input_name]
            submit_results[input_name] = child.submit(submission)
            child.save()
            completed = completed and submit_results[input_name]

        self.completed = bool(completed)

        return {
            'submitResults': submit_results,
            'completed': self.completed,
        }

    def studio_view(self, context):
        return Fragment(u'Studio view body')

    @staticmethod
    def workbench_scenarios():
        """
        Sample scenarios which will be displayed in the workbench
        """
        return [
            ("Mentoring: Pre-Goal Brainstom", load_resource('templates/001_pre_goal_brainstorm.xml')),
            ("Mentoring: Getting Feedback", load_resource('templates/002_getting_feedback.xml')),
        ]
